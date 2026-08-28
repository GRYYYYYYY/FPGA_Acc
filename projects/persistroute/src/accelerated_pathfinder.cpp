#include "accelerated_pathfinder.hpp"

#include <algorithm>
#include <chrono>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <tuple>

namespace persistroute {
namespace {

void add_telemetry(KernelBatchTelemetry& dst,const KernelBatchTelemetry& src) {
 dst.h2d_bytes+=src.h2d_bytes;dst.d2h_bytes+=src.d2h_bytes;
 dst.search_ns+=src.search_ns;dst.commit_ns+=src.commit_ns;
 dst.search_launches+=src.search_launches;dst.commit_launches+=src.commit_launches;
}

std::uint16_t sat16(std::uint64_t value) {
 return static_cast<std::uint16_t>(std::min<std::uint64_t>(value, 65535U));
}

std::uint64_t hash_word(std::uint64_t hash, std::uint64_t value) {
 for (unsigned byte = 0; byte < 8; ++byte) {
  hash ^= (value >> (byte * 8U)) & 0xffU;
  hash *= 1099511628211ULL;
 }
 return hash;
}

std::uint64_t hash_resources(const std::vector<Resource>& resources) {
 std::uint64_t hash = 1469598103934665603ULL;
 for (const auto& r : resources) {
  hash=hash_word(hash,r.occupancy);hash=hash_word(hash,r.capacity);
  hash=hash_word(hash,r.present_cost_q);hash=hash_word(hash,r.history_cost_q);
  hash=hash_word(hash,r.version);hash=hash_word(hash,r.owner);
 }
 return hash;
}

std::uint64_t hash_routes(const std::vector<RoutedTask>& tasks) {
 std::uint64_t hash = 1469598103934665603ULL;
 for (const auto& routed : tasks) {
  hash=hash_word(hash,routed.task.id);hash=hash_word(hash,routed.routed?1U:0U);
  hash=hash_word(hash,routed.path.size());
  for (const auto node : routed.path) hash=hash_word(hash,node);
 }
 return hash;
}

struct TreeState {
 std::uint32_t net_id = INVALID_RESOURCE;
 std::uint32_t source = INVALID_RESOURCE;
 std::map<std::uint32_t,std::uint32_t> parent;
 std::vector<std::size_t> tasks;
};

class Owners {
public:
 Owners(const std::vector<Resource>& initial,std::vector<Resource>& current)
     : initial_(initial),current_(current),dynamic_(initial.size()) {}

 void add(std::uint32_t node,std::uint32_t net) {dynamic_[node].insert(net);}
 void remove(std::uint32_t node,std::uint32_t net) {dynamic_[node].erase(net);}
 const std::set<std::uint32_t>& at(std::uint32_t node) const {return dynamic_[node];}

 void refresh_all() {
  for (std::size_t node=0;node<current_.size();++node) {
   const Resource& base=initial_[node];Resource& state=current_[node];
   std::uint32_t occupancy=base.occupancy;std::set<std::uint32_t> known=dynamic_[node];
   if(base.occupancy&&base.owner!=INVALID_RESOURCE)known.insert(base.owner);
   for(const auto net:dynamic_[node])if(!(base.occupancy&&base.owner==net))++occupancy;
   const std::uint16_t next=sat16(occupancy);
   const std::uint32_t owner=next==1&&known.size()==1?*known.begin():INVALID_RESOURCE;
   if(state.occupancy!=next||state.owner!=owner){state.occupancy=next;state.owner=owner;++state.version;}
  }
 }

private:
 const std::vector<Resource>& initial_;
 std::vector<Resource>& current_;
 std::vector<std::set<std::uint32_t>> dynamic_;
};

void validate_inputs(const std::vector<Node>& nodes,const std::vector<Edge>& edges,
 const std::vector<Resource>& resources,const std::vector<Task>& tasks,
 const PathfinderConfig& config) {
 if(nodes.empty()||nodes.size()!=resources.size()||config.max_iterations==0||
    config.min_timing_iterations==0||config.min_timing_iterations>config.max_iterations||
    config.timing_update_period==0||config.present_multiplier_q==0)throw std::invalid_argument("invalid accelerated PathFinder sizes/config");
 for(std::size_t node=0;node<nodes.size();++node){
  if(resources[node].capacity==0||static_cast<std::uint64_t>(nodes[node].edge_begin)+nodes[node].edge_count>edges.size())
   throw std::invalid_argument("invalid accelerated PathFinder graph/resource");
 }
 std::set<std::uint32_t> ids;std::map<std::uint32_t,std::uint32_t> sources;
 for(const auto& task:tasks){
  if(task.source>=nodes.size()||task.sink>=nodes.size()||!ids.insert(task.id).second)
   throw std::invalid_argument("invalid accelerated PathFinder task");
  const auto inserted=sources.emplace(task.net_id,task.source);
  if(!inserted.second&&inserted.first->second!=task.source)
   throw std::invalid_argument("one net has multiple sources");
 }
 for(const auto& edge:edges)if(edge.dst>=nodes.size())throw std::invalid_argument("edge destination out of range");
}

void update_costs(std::vector<Resource>& resources,std::uint16_t present,std::uint16_t history_step) {
 for(auto& state:resources){
  const std::uint32_t over=state.occupancy>state.capacity?state.occupancy-state.capacity:0U;
  const std::uint16_t history=sat16(static_cast<std::uint64_t>(state.history_cost_q)+
                                   static_cast<std::uint64_t>(history_step)*over);
  if(state.present_cost_q!=present||state.history_cost_q!=history){
   state.present_cost_q=present;state.history_cost_q=history;++state.version;
  }
 }
}

std::vector<std::uint32_t> prefix_to(const TreeState& tree,std::uint32_t attachment) {
 std::vector<std::uint32_t> reverse;
 while(attachment!=tree.source){
  reverse.push_back(attachment);const auto found=tree.parent.find(attachment);
  if(found==tree.parent.end()||found->second==INVALID_RESOURCE)throw std::logic_error("broken accelerated route tree");
  attachment=found->second;
 }
 return std::vector<std::uint32_t>(reverse.rbegin(),reverse.rend());
}

void accept_path(TreeState& tree,Owners& owners,RoutedTask& routed,std::uint32_t attachment,const std::vector<std::uint32_t>& branch) {
 if(!tree.parent.count(attachment)||(branch.empty()&&attachment!=routed.task.sink)||
    (!branch.empty()&&branch.back()!=routed.task.sink))throw std::runtime_error("kernel returned an invalid tree branch");
 std::uint32_t parent=attachment;
 for(const std::uint32_t child:branch){
  if(!tree.parent.emplace(child,parent).second)throw std::logic_error("route branch re-entered its tree");
  owners.add(child,tree.net_id);parent=child;
 }
 routed.path=prefix_to(tree,attachment);routed.path.insert(routed.path.end(),branch.begin(),branch.end());
 routed.routed=true;
}

std::vector<SearchSeed> tree_seeds(const TreeState& tree) {
 std::map<std::uint32_t,std::uint32_t> depths;depths[tree.source]=0;
 for(const auto& item:tree.parent){std::uint32_t node=item.first;std::vector<std::uint32_t> chain;
  while(!depths.count(node)){const auto found=tree.parent.find(node);if(found==tree.parent.end()||found->second==INVALID_RESOURCE||chain.size()>tree.parent.size())throw std::logic_error("broken tree depth");chain.push_back(node);node=found->second;}
  std::uint32_t depth=depths[node];for(auto it=chain.rbegin();it!=chain.rend();++it)depths[*it]=++depth;
 }
 std::vector<SearchSeed> seeds;for(const auto& item:depths)seeds.push_back({item.first,item.second});return seeds;
}

std::uint64_t tree_wirelength(const TreeState& tree,const std::vector<Node>& nodes) {
 std::uint64_t total=0;for(const auto& item:tree.parent)total+=nodes[item.first].delay_class;return total;
}

std::uint64_t routed_delay(const RoutedTask& routed,const std::vector<Node>& nodes,
 const std::vector<Edge>& edges) {
 std::uint64_t total=0;std::uint32_t src=routed.task.source;
 for(const auto dst:routed.path){const Node node=nodes[src];bool found=false;
  for(std::uint32_t j=0;j<node.edge_count;++j){const Edge& edge=edges[node.edge_begin+j];if(edge.dst==dst){total+=edge.delay_q;found=true;break;}}
  if(!found)throw std::logic_error("routed cleanup path is not present in the RR graph");
  src=dst;
 }
 return total;
}

void ripup(TreeState& tree,Owners& owners,std::vector<RoutedTask>& tasks,PathfinderMetrics& metrics) {
 if(tree.parent.size()>1)++metrics.ripups;
 for(const auto& item:tree.parent)if(item.first!=tree.source)owners.remove(item.first,tree.net_id);
 tree.parent.clear();tree.parent[tree.source]=INVALID_RESOURCE;
 for(const auto index:tree.tasks){if(tasks[index].routed)++metrics.ripped_connections;tasks[index].routed=false;tasks[index].path.clear();}
}

void update_timing(std::uint32_t iteration,const std::vector<Node>& nodes,
 const std::vector<Edge>& edges,std::vector<RoutedTask>& tasks,
 const TimingAnalyzer& analyzer,std::vector<PathfinderTimingIteration>& log) {
 if(!analyzer)return;
 const auto analysis=analyzer(iteration,nodes,edges,tasks);
 if(analysis.connections.size()!=tasks.size())throw std::runtime_error("timing analyzer must return exactly one update per connection");
 std::map<std::uint32_t,TimingConnectionUpdate> updates;
 for(const auto& update:analysis.connections)if(!updates.emplace(update.task_id,update).second)throw std::runtime_error("timing analyzer returned a duplicate task ID");
 PathfinderTimingIteration item{};item.iteration=iteration;item.min_criticality_q=65535U;item.critical_path_delay_ps=analysis.critical_path_delay_ps;
 for(auto& routed:tasks){const auto found=updates.find(routed.task.id);if(found==updates.end())throw std::runtime_error("timing analyzer omitted a task ID");if(routed.task.criticality_q!=found->second.criticality_q)++item.updated_connections;routed.task.criticality_q=found->second.criticality_q;item.min_criticality_q=std::min(item.min_criticality_q,routed.task.criticality_q);item.max_criticality_q=std::max(item.max_criticality_q,routed.task.criticality_q);}
 if(tasks.empty())item.min_criticality_q=0;
 log.push_back(item);
}

} // namespace

AcceleratedPathfinderResult route_accelerated_pathfinder(
 const std::vector<Node>& nodes,const std::vector<Edge>& edges,
 const std::vector<Resource>& initial_resources,const std::vector<Task>& input_tasks,
 const KernelBatchExecutor& executor,const PathfinderConfig& config,std::uint32_t issue_width,
 const TimingAnalyzer& timing_analyzer,const SelectiveCleanupConfig& cleanup) {
 validate_inputs(nodes,edges,initial_resources,input_tasks,config);
 if(!executor||issue_width==0)throw std::invalid_argument("accelerated PathFinder executor/issue width is invalid");
 AcceleratedPathfinderResult out;auto& result=out.routing;result.resources=initial_resources;
 for(const auto& task:input_tasks)result.tasks.push_back({task,{},false});
 Owners owners(initial_resources,result.resources);std::map<std::uint32_t,TreeState> trees;
 for(std::size_t i=0;i<result.tasks.size();++i){const Task& task=result.tasks[i].task;auto& tree=trees[task.net_id];tree.net_id=task.net_id;tree.source=task.source;tree.parent[task.source]=INVALID_RESOURCE;tree.tasks.push_back(i);}
 for(auto& item:trees)std::sort(item.second.tasks.begin(),item.second.tasks.end(),[&](auto a,auto b){const Task& x=result.tasks[a].task;const Task& y=result.tasks[b].task;return std::tie(x.priority,x.id)<std::tie(y.priority,y.id);});
 std::vector<std::uint32_t> net_order;for(const auto& item:trees)net_order.push_back(item.first);
 std::sort(net_order.begin(),net_order.end(),[&](auto a,auto b){const Task& x=result.tasks[trees[a].tasks.front()].task;const Task& y=result.tasks[trees[b].tasks.front()].task;return std::tie(x.priority,x.id,a)<std::tie(y.priority,y.id,b);});
 std::set<std::uint32_t> pending;for(const auto net:net_order)pending.insert(net);
 std::uint16_t present=config.present_start_q;update_costs(result.resources,present,0);

 for(std::uint32_t iteration=0;iteration<config.max_iterations;++iteration){
  result.metrics.iterations=iteration+1;PathfinderIteration log{iteration,static_cast<std::uint32_t>(pending.size()),0,0,present};
  AcceleratedIteration audit{};audit.iteration=iteration;
  if(iteration){for(const auto net:net_order)if(pending.count(net))ripup(trees[net],owners,result.tasks,result.metrics);owners.refresh_all();}
  std::map<std::uint32_t,std::size_t> cursors;for(const auto net:pending)cursors[net]=0;
  while(true){
   std::vector<Task> wave;std::vector<std::vector<SearchSeed>> seeds;
   for(const auto net:net_order){if(!pending.count(net))continue;auto& tree=trees[net];auto& cursor=cursors[net];if(cursor<tree.tasks.size()){Task task=result.tasks[tree.tasks[cursor++]].task;task.epoch=iteration;wave.push_back(task);seeds.push_back(tree_seeds(tree));}}
   if(wave.empty())break;
   ++audit.waves;audit.launched+=wave.size();result.metrics.searches+=wave.size();
   for(std::size_t begin=0;begin<wave.size();begin+=issue_width){
    const std::size_t end=std::min<std::size_t>(wave.size(),begin+issue_width);
    std::vector<Task> batch_tasks(wave.begin()+begin,wave.begin()+end);
    std::vector<std::vector<SearchSeed>> batch_seeds(seeds.begin()+begin,seeds.begin()+end);
    KernelBatchResult batch=executor(nodes,edges,result.resources,batch_tasks,batch_seeds,true);
    add_telemetry(audit.telemetry,batch.telemetry);add_telemetry(out.telemetry,batch.telemetry);
    result.metrics.expanded+=batch.search_metrics.expanded;result.metrics.edge_visits+=batch.search_metrics.edge_visits;
    std::map<std::uint32_t,const KernelCandidate*> by_id;for(const auto& candidate:batch.candidates)by_id[candidate.task.id]=&candidate;
    for(const auto& task:batch_tasks){
     const auto found=by_id.find(task.id);auto& tree=trees[task.net_id];
     const auto index=*std::find_if(tree.tasks.begin(),tree.tasks.end(),[&](auto i){return result.tasks[i].task.id==task.id;});
     RoutedTask& routed=result.tasks[index];routed.task.epoch=iteration;
     if(found==by_id.end()||found->second->search_status!=1||found->second->commit_status!=4){++audit.failed;++log.failed_connections;continue;}
     accept_path(tree,owners,routed,found->second->attachment,found->second->path);++audit.committed;
    }
    owners.refresh_all();
   }
  }
  const std::uint32_t over=static_cast<std::uint32_t>(std::count_if(result.resources.begin(),result.resources.end(),[](const auto& r){return r.occupancy>r.capacity;}));
  log.overused_resources=over;audit.overused_resources=over;audit.resource_hash=hash_resources(result.resources);audit.route_hash=hash_routes(result.tasks);
  result.metrics.overused_resources=over;result.iteration_log.push_back(log);out.audit.push_back(audit);
  bool timing_updated=timing_analyzer&&iteration%config.timing_update_period==0;
  if(timing_updated){const auto timing_begin=std::chrono::steady_clock::now();update_timing(iteration,nodes,edges,result.tasks,timing_analyzer,result.timing_log);out.timing_ns+=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-timing_begin).count();}
  if(timing_updated){
   for(auto& item:trees)std::sort(item.second.tasks.begin(),item.second.tasks.end(),[&](auto lhs,auto rhs){const Task& a=result.tasks[lhs].task;const Task& b=result.tasks[rhs].task;return std::make_tuple(65535U-a.criticality_q,a.priority,a.id)<std::make_tuple(65535U-b.criticality_q,b.priority,b.id);});
   std::sort(net_order.begin(),net_order.end(),[&](auto lhs,auto rhs){const Task& a=result.tasks[trees[lhs].tasks.front()].task;const Task& b=result.tasks[trees[rhs].tasks.front()].task;return std::make_tuple(65535U-a.criticality_q,a.priority,a.id,lhs)<std::make_tuple(65535U-b.criticality_q,b.priority,b.id,rhs);});
  }
  const bool all=std::all_of(result.tasks.begin(),result.tasks.end(),[](const auto& task){return task.routed;});
  const bool force_timing_reroute=timing_analyzer&&iteration+1<config.min_timing_iterations;
  if(all&&over==0&&!force_timing_reroute){if(timing_analyzer&&!timing_updated){const auto timing_begin=std::chrono::steady_clock::now();update_timing(iteration,nodes,edges,result.tasks,timing_analyzer,result.timing_log);out.timing_ns+=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-timing_begin).count();}result.route_success=true;break;}if(iteration+1==config.max_iterations)break;
  const std::uint64_t grown=(static_cast<std::uint64_t>(present)*config.present_multiplier_q+128U)/256U;
  present=std::max<std::uint16_t>(1,sat16(grown));update_costs(result.resources,present,config.history_increment_q);
  std::set<std::uint32_t> next;if(force_timing_reroute)next.insert(net_order.begin(),net_order.end());for(const auto& task:result.tasks)if(!task.routed)next.insert(task.task.net_id);
  for(std::size_t node=0;node<result.resources.size();++node)if(result.resources[node].occupancy>result.resources[node].capacity)for(const auto net:owners.at(node))next.insert(net);
  pending.swap(next);
 }
 if(result.route_success&&cleanup.passes&&cleanup.channel_length_cost_q){
  const auto cleanup_begin=std::chrono::steady_clock::now();
  std::vector<Edge> cleanup_edges=edges;
  for(auto& edge:cleanup_edges){const std::uint32_t length=nodes[edge.dst].delay_class;
   const std::uint64_t extra=length>0?static_cast<std::uint64_t>(cleanup.channel_length_cost_q)*(length-1U):0U;
   edge.base_cost_q=sat16(static_cast<std::uint64_t>(edge.base_cost_q)+extra);
  }
  auto total_wire=[&](){std::uint64_t total=0;for(const auto& item:trees)total+=tree_wirelength(item.second,nodes);return total;};
  out.cleanup_wirelength_before=total_wire();
  const bool branch_mode=cleanup.branch_budget_ppm||cleanup.max_branches;
  const std::uint64_t scaled_branch_limit=(static_cast<std::uint64_t>(result.tasks.size())*cleanup.branch_budget_ppm+999999ULL)/1000000ULL;
  const std::uint32_t branch_limit=cleanup.max_branches?cleanup.max_branches:static_cast<std::uint32_t>(std::min<std::uint64_t>(scaled_branch_limit,0xffffffffULL));
  for(std::uint32_t pass=0;pass<cleanup.passes;++pass){
   if(branch_mode){
    struct BranchItem{std::uint64_t score;std::size_t index;};std::vector<BranchItem> order;
    for(const auto& tree_item:trees){const TreeState& tree=tree_item.second;std::map<std::uint32_t,std::uint32_t> uses;for(const auto task_index:tree.tasks)for(const auto node:result.tasks[task_index].path)++uses[node];
     for(const auto task_index:tree.tasks){const auto& path=result.tasks[task_index].path;std::uint64_t unique_wire=0;std::size_t unique_nodes=0;for(auto it=path.rbegin();it!=path.rend()&&uses[*it]==1;++it){unique_wire+=nodes[*it].delay_class;++unique_nodes;}if(unique_nodes)order.push_back({unique_wire*1000000ULL/unique_nodes,task_index});}}
    std::sort(order.begin(),order.end(),[](const auto& lhs,const auto& rhs){return std::make_tuple(std::numeric_limits<std::uint64_t>::max()-lhs.score,lhs.index)<std::make_tuple(std::numeric_limits<std::uint64_t>::max()-rhs.score,rhs.index);});
    std::uint32_t accepted_this_pass=0;
    for(const auto& item:order){
     if(out.cleanup_attempted_branches>=branch_limit)break;
     if(cleanup.time_budget_ms&&std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-cleanup_begin).count()>=cleanup.time_budget_ms)break;
     ++out.cleanup_attempted_branches;RoutedTask& routed=result.tasks[item.index];TreeState& tree=trees[routed.task.net_id];
     std::map<std::uint32_t,std::uint32_t> uses;for(const auto task_index:tree.tasks)for(const auto node:result.tasks[task_index].path)++uses[node];
     std::vector<std::uint32_t> suffix;for(auto it=routed.path.rbegin();it!=routed.path.rend()&&uses[*it]==1;++it)suffix.push_back(*it);if(suffix.empty())continue;
     const std::uint64_t old_wire=tree_wirelength(tree,nodes),old_delay=routed_delay(routed,nodes,edges);const TreeState old_tree=tree;
     std::vector<RoutedTask> old_tasks;old_tasks.reserve(tree.tasks.size());for(const auto task_index:tree.tasks)old_tasks.push_back(result.tasks[task_index]);const std::vector<Resource> old_resources=result.resources;
     for(const auto node:suffix){owners.remove(node,tree.net_id);tree.parent.erase(node);}routed.routed=false;routed.path.clear();owners.refresh_all();
     Task task=routed.task;task.epoch=result.metrics.iterations+pass+1;KernelBatchResult batch=executor(nodes,cleanup_edges,result.resources,{task},{tree_seeds(tree)},false);++result.metrics.searches;add_telemetry(out.telemetry,batch.telemetry);result.metrics.expanded+=batch.search_metrics.expanded;result.metrics.edge_visits+=batch.search_metrics.edge_visits;
     bool complete=batch.candidates.size()==1&&batch.candidates[0].search_status==1&&batch.candidates[0].commit_status==4;
     if(complete){const auto& candidate=batch.candidates[0];accept_path(tree,owners,routed,candidate.attachment,candidate.path);owners.refresh_all();}
     const std::uint64_t tolerance=old_delay*cleanup.delay_tolerance_ppm/1000000ULL;const bool delay_ok=complete&&routed_delay(routed,nodes,edges)<=old_delay+tolerance;
     const bool feasible=complete&&std::none_of(result.resources.begin(),result.resources.end(),[](const auto& state){return state.occupancy>state.capacity;});
     if(feasible&&delay_ok&&tree_wirelength(tree,nodes)<old_wire){++out.cleanup_accepted_branches;++accepted_this_pass;}
     else {ripup(tree,owners,result.tasks,result.metrics);tree=old_tree;for(const auto& parent:tree.parent)if(parent.first!=tree.source)owners.add(parent.first,tree.net_id);for(std::size_t i=0;i<tree.tasks.size();++i)result.tasks[tree.tasks[i]]=old_tasks[i];owners.refresh_all();result.resources=old_resources;}
    }
    if(accepted_this_pass==0||out.cleanup_attempted_branches>=branch_limit)break;
    continue;
   }
   std::vector<std::uint32_t> order=net_order;
   std::sort(order.begin(),order.end(),[&](auto lhs,auto rhs){const auto a=tree_wirelength(trees[lhs],nodes),b=tree_wirelength(trees[rhs],nodes);return std::make_tuple(std::numeric_limits<std::uint64_t>::max()-a,lhs)<std::make_tuple(std::numeric_limits<std::uint64_t>::max()-b,rhs);});
   std::uint32_t accepted_this_pass=0;
   for(const auto net:order){++out.cleanup_attempted_nets;TreeState& tree=trees[net];
    const std::uint64_t old_wire=tree_wirelength(tree,nodes);if(old_wire==0)continue;
    std::vector<std::uint64_t> old_delays;old_delays.reserve(tree.tasks.size());for(const auto index:tree.tasks)old_delays.push_back(routed_delay(result.tasks[index],nodes,edges));
    const TreeState old_tree=tree;std::vector<RoutedTask> old_tasks;old_tasks.reserve(tree.tasks.size());for(const auto index:tree.tasks)old_tasks.push_back(result.tasks[index]);
    const std::vector<Resource> old_resources=result.resources;
    ripup(tree,owners,result.tasks,result.metrics);owners.refresh_all();bool complete=true;
    for(const auto index:tree.tasks){RoutedTask& routed=result.tasks[index];Task task=routed.task;task.epoch=result.metrics.iterations+pass+1;
     const std::vector<Task> one_task{task};const std::vector<std::vector<SearchSeed>> one_seed{tree_seeds(tree)};
     KernelBatchResult batch=executor(nodes,cleanup_edges,result.resources,one_task,one_seed,false);++result.metrics.searches;
     add_telemetry(out.telemetry,batch.telemetry);
     result.metrics.expanded+=batch.search_metrics.expanded;result.metrics.edge_visits+=batch.search_metrics.edge_visits;
     if(batch.candidates.size()!=1||batch.candidates[0].search_status!=1||batch.candidates[0].commit_status!=4){complete=false;break;}
     const auto& candidate=batch.candidates[0];accept_path(tree,owners,routed,candidate.attachment,candidate.path);owners.refresh_all();
    }
    bool delay_ok=complete;if(complete&&cleanup.per_connection_delay_guard)for(std::size_t i=0;i<tree.tasks.size();++i){const std::uint64_t old_delay=old_delays[i];const std::uint64_t tolerance=old_delay*cleanup.delay_tolerance_ppm/1000000ULL;if(routed_delay(result.tasks[tree.tasks[i]],nodes,edges)>old_delay+tolerance){delay_ok=false;break;}}
    if(complete&&!cleanup.per_connection_delay_guard){const std::uint64_t old_delay=*std::max_element(old_delays.begin(),old_delays.end());std::uint64_t new_delay=0;for(const auto index:tree.tasks)new_delay=std::max(new_delay,routed_delay(result.tasks[index],nodes,edges));const std::uint64_t tolerance=old_delay*cleanup.delay_tolerance_ppm/1000000ULL;delay_ok=new_delay<=old_delay+tolerance;}
    const bool feasible=complete&&std::none_of(result.resources.begin(),result.resources.end(),[](const auto& state){return state.occupancy>state.capacity;});
    const bool improve=feasible&&delay_ok&&tree_wirelength(tree,nodes)<old_wire;
    if(improve){++out.cleanup_accepted_nets;++accepted_this_pass;}
    else {ripup(tree,owners,result.tasks,result.metrics);tree=old_tree;for(const auto& item:tree.parent)if(item.first!=tree.source)owners.add(item.first,tree.net_id);for(std::size_t i=0;i<tree.tasks.size();++i)result.tasks[tree.tasks[i]]=old_tasks[i];owners.refresh_all();result.resources=old_resources;}
   }
   if(accepted_this_pass==0)break;
  }
  out.cleanup_wirelength_after=total_wire();result.metrics.overused_resources=0;
  out.cleanup_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-cleanup_begin).count();
 }
 for(const auto& item:trees){const auto& tree=item.second;NetRouteTree snapshot{tree.net_id,tree.source,{},{}};for(const auto& edge:tree.parent){snapshot.nodes.push_back(edge.first);if(edge.second!=INVALID_RESOURCE)snapshot.edges.push_back({edge.second,edge.first});}std::sort(snapshot.edges.begin(),snapshot.edges.end(),[](const auto& a,const auto& b){return std::tie(a.parent,a.child)<std::tie(b.parent,b.child);});result.route_trees.push_back(std::move(snapshot));}
 result.legal=result.route_success&&validate_pathfinder_result(nodes,edges,initial_resources,result);
 return out;
}

} // namespace persistroute
