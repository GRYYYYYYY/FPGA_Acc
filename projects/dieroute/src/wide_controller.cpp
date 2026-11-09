// Ported from ../persistroute/src/accelerated_pathfinder.cpp
// Source SHA-256: bc02685f60db5ee761454a086bd80074d0d55cfed1acc451dd642352b71c80e7
// Reuses PR scheduling, tree ownership, rip-up, timing and native validation.
// Changes: authoritative u64 cost sidecar, checked updates/versions/seeds,
// u64 iteration factors. Optional cleanup is not part of this API.
#include "wide_costs.hpp"

#include <algorithm>
#include <chrono>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <tuple>

namespace dieroute {
using namespace persistroute;
namespace {

void add_telemetry(KernelBatchTelemetry& dst,const KernelBatchTelemetry& src) {
 dst.h2d_bytes+=src.h2d_bytes;dst.d2h_bytes+=src.d2h_bytes;
 dst.search_ns+=src.search_ns;dst.commit_ns+=src.commit_ns;
 dst.search_launches+=src.search_launches;dst.commit_launches+=src.commit_launches;
}

std::uint64_t hash_word(std::uint64_t hash, std::uint64_t value) {
 for (unsigned byte = 0; byte < 8; ++byte) {
  hash ^= (value >> (byte * 8U)) & 0xffU;
  hash *= 1099511628211ULL;
 }
 return hash;
}

std::uint64_t hash_resources(const std::vector<Resource>& resources,const std::vector<WideCost>& costs) {
 std::uint64_t hash = 1469598103934665603ULL;
 for (std::size_t i=0;i<resources.size();++i) {
  const auto& r=resources[i];
  hash=hash_word(hash,r.occupancy);hash=hash_word(hash,r.capacity);
  hash=hash_word(hash,costs[i].present_q);hash=hash_word(hash,costs[i].history_q);
  hash=hash_word(hash,r.version);hash=hash_word(hash,r.owner);
 }
 return hash;
}

std::uint64_t hash_routes(const std::vector<RoutedTask>& tasks,const std::vector<std::vector<std::uint32_t>>* edge_paths) {
 std::uint64_t hash = 1469598103934665603ULL;
 for (std::size_t i=0;i<tasks.size();++i) {const auto& routed=tasks[i];
  hash=hash_word(hash,routed.task.id);hash=hash_word(hash,routed.routed?1U:0U);
  hash=hash_word(hash,routed.path.size());
  for (const auto node : routed.path) hash=hash_word(hash,node);
  if(edge_paths){hash=hash_word(hash,edge_paths->at(i).size());for(auto e:edge_paths->at(i))hash=hash_word(hash,e);}
 }
 return hash;
}

struct TreeState {
 std::uint32_t net_id = INVALID_RESOURCE;
 std::uint32_t source = INVALID_RESOURCE;
 std::map<std::uint32_t,std::uint32_t> parent;
 std::map<std::uint32_t,std::uint32_t> parent_edge;
 std::map<std::uint32_t,std::uint32_t> depth;
 std::map<std::uint32_t,std::uint64_t> delay_q;
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
   if(occupancy>65535U)throw std::overflow_error("wide controller occupancy overflow");
   const auto next=static_cast<std::uint16_t>(occupancy);
   const std::uint32_t owner=next==1&&known.size()==1?*known.begin():INVALID_RESOURCE;
   if(state.occupancy!=next||state.owner!=owner){if(state.version==0xffffffffU)throw std::overflow_error("wide controller owner version overflow");state.occupancy=next;state.owner=owner;++state.version;}
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

std::vector<std::uint32_t> prefix_to(const TreeState& tree,std::uint32_t attachment) {
 std::vector<std::uint32_t> reverse;
 while(attachment!=tree.source){
  reverse.push_back(attachment);const auto found=tree.parent.find(attachment);
  if(found==tree.parent.end()||found->second==INVALID_RESOURCE)throw std::logic_error("broken accelerated route tree");
  attachment=found->second;
 }
 return std::vector<std::uint32_t>(reverse.rbegin(),reverse.rend());
}

std::uint16_t edge_delay(std::uint32_t source,std::uint32_t sink,
 const std::vector<Node>& nodes,const std::vector<Edge>& edges) {
 const Node node=nodes[source];
 for(std::uint32_t j=0;j<node.edge_count;++j){const Edge& edge=edges[node.edge_begin+j];if(edge.dst==sink)return edge.delay_q;}
 throw std::logic_error("route-tree edge is not present in the RR graph");
}

void accept_path(TreeState& tree,Owners& owners,RoutedTask& routed,std::uint32_t attachment,
 const std::vector<std::uint32_t>& branch,const std::vector<Node>& nodes,const std::vector<Edge>& edges,
 const std::vector<std::uint32_t>* branch_edges,std::vector<std::uint32_t>* task_edges) {
 if(!tree.parent.count(attachment)||(branch.empty()&&attachment!=routed.task.sink)||
    (!branch.empty()&&branch.back()!=routed.task.sink))throw std::runtime_error("kernel returned an invalid tree branch");
 if(branch_edges && !valid_edge_path(nodes,edges,attachment,branch,*branch_edges))throw std::runtime_error("invalid selected CSR edge trace");
 auto prefix=prefix_to(tree,attachment);
 if(task_edges){task_edges->clear();for(auto n:prefix)task_edges->push_back(tree.parent_edge.at(n));}
 std::set<std::uint32_t> unique;
 for(auto child:branch)if(tree.parent.count(child)||!unique.insert(child).second)throw std::logic_error("route branch re-entered its tree");
 std::uint32_t parent=attachment;
 for(std::size_t j=0;j<branch.size();++j){const auto child=branch[j];
  if(!tree.parent.emplace(child,parent).second)throw std::logic_error("route branch re-entered its tree");
  tree.depth[child]=tree.depth.at(parent)+1U;
  tree.delay_q[child]=tree.delay_q.at(parent)+(branch_edges?edges[branch_edges->at(j)].delay_q:edge_delay(parent,child,nodes,edges));
  if(branch_edges){tree.parent_edge[child]=branch_edges->at(j);task_edges->push_back(branch_edges->at(j));}
  owners.add(child,tree.net_id);parent=child;
 }
 routed.path=std::move(prefix);routed.path.insert(routed.path.end(),branch.begin(),branch.end());
 routed.routed=true;
}

std::vector<SearchSeed> tree_seeds(const TreeState& tree,std::uint16_t criticality_q,std::uint16_t timing_weight_q) {
 if(tree.parent.size()!=tree.depth.size()||tree.parent.size()!=tree.delay_q.size())throw std::logic_error("broken route-tree timing cache");
 std::vector<SearchSeed> seeds;seeds.reserve(tree.parent.size());
 for(const auto& item:tree.parent){const std::uint64_t timing=
   tree.delay_q.at(item.first)*criticality_q/65535U;
  const std::uint64_t weighted=timing*timing_weight_q/256U;
  if(weighted>0xffffffffULL)throw std::overflow_error("tree seed cost exceeds PR seed ABI");
  seeds.push_back({item.first,tree.depth.at(item.first),static_cast<std::uint32_t>(weighted)});}
 return seeds;
}

void ripup(TreeState& tree,Owners& owners,std::vector<RoutedTask>& tasks,PathfinderMetrics& metrics,
 std::vector<std::vector<std::uint32_t>>* task_edges) {
 if(tree.parent.size()>1)++metrics.ripups;
 for(const auto& item:tree.parent)if(item.first!=tree.source)owners.remove(item.first,tree.net_id);
 tree.parent.clear();tree.parent_edge.clear();tree.depth.clear();tree.delay_q.clear();
 tree.parent[tree.source]=INVALID_RESOURCE;tree.depth[tree.source]=0;tree.delay_q[tree.source]=0;
 for(const auto index:tree.tasks){if(tasks[index].routed)++metrics.ripped_connections;tasks[index].routed=false;tasks[index].path.clear();if(task_edges)task_edges->at(index).clear();}
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

static WidePathfinderResult route_wide_impl(
 const std::vector<Node>& nodes,const std::vector<Edge>& edges,
 const std::vector<Resource>& initial_resources,const std::vector<Task>& input_tasks,
 const WideBatchExecutor& executor,const PathfinderConfig& config,std::uint32_t issue_width,
 const TimingAnalyzer& legacy_timing,const EdgeBatchExecutor* edge_executor,const EdgeTimingAnalyzer& edge_timing,RoutingPolicyPtr policy) {
 validate_inputs(nodes,edges,initial_resources,input_tasks,config);
 if(policy){policy->validate(nodes.size(),edges.size());
  if(policy->active()&&!edge_executor)throw std::invalid_argument("routing policy requires edge-aware controller");
  for(const auto& task:input_tasks)if(!policy->node_allowed(task.source,task.net_id)||!policy->node_allowed(task.sink,task.net_id))throw std::invalid_argument("task terminal forbidden by routing policy");}
 const bool adaptive=(config.adaptive_issue_width_min!=0||config.adaptive_issue_stagnation_iterations!=0);
 if((!executor&&!edge_executor)||(edge_executor&&!*edge_executor)||issue_width==0||(adaptive&&(config.adaptive_issue_width_min==0||
    config.adaptive_issue_stagnation_iterations==0||config.adaptive_issue_width_min>issue_width)))
  throw std::invalid_argument("accelerated PathFinder executor/issue width is invalid");
 WidePathfinderResult wide;auto& out=wide.result;auto& costs=wide.costs;
 wide.edge_identity=edge_executor!=nullptr;
 if(wide.edge_identity)wide.task_edges.resize(input_tasks.size());
 TimingAnalyzer timing_analyzer=legacy_timing;
 if(edge_executor && legacy_timing)throw std::invalid_argument("edge mode requires edge-aware timing analyzer");
 if(edge_executor && edge_timing)timing_analyzer=[&](auto iteration,const auto& n,const auto& e,const auto& t){return edge_timing(iteration,n,e,t,wide.task_edges);};
 auto& result=out.routing;result.resources=initial_resources;
 for(auto& r:result.resources){costs.push_back({r.present_cost_q,r.history_cost_q});r.present_cost_q=0;r.history_cost_q=0;}
 for(const auto& task:input_tasks)result.tasks.push_back({task,{},false});
 Owners owners(initial_resources,result.resources);std::map<std::uint32_t,TreeState> trees;
 for(std::size_t i=0;i<result.tasks.size();++i){const Task& task=result.tasks[i].task;auto& tree=trees[task.net_id];tree.net_id=task.net_id;tree.source=task.source;tree.parent[task.source]=INVALID_RESOURCE;tree.depth[task.source]=0;tree.delay_q[task.source]=0;tree.tasks.push_back(i);}
 for(auto& item:trees)std::sort(item.second.tasks.begin(),item.second.tasks.end(),[&](auto a,auto b){const Task& x=result.tasks[a].task;const Task& y=result.tasks[b].task;return std::tie(x.priority,x.id)<std::tie(y.priority,y.id);});
 std::vector<std::uint32_t> net_order;for(const auto& item:trees)net_order.push_back(item.first);
 std::sort(net_order.begin(),net_order.end(),[&](auto a,auto b){const Task& x=result.tasks[trees[a].tasks.front()].task;const Task& y=result.tasks[trees[b].tasks.front()].task;return std::tie(x.priority,x.id,a)<std::tie(y.priority,y.id,b);});
 std::set<std::uint32_t> pending;for(const auto net:net_order)pending.insert(net);
 std::uint64_t present=config.present_start_q;update_wide_costs(result.resources,costs,present,0,policy.get());
 std::uint32_t current_issue_width=issue_width;
 std::uint32_t best_overuse=std::numeric_limits<std::uint32_t>::max(),stagnant_iterations=0;

 for(std::uint32_t iteration=0;iteration<config.max_iterations;++iteration){
  result.metrics.iterations=iteration+1;PathfinderIteration log{iteration,static_cast<std::uint32_t>(pending.size()),0,0,0};
  wide.present_factors.push_back(present);
  AcceleratedIteration audit{};audit.iteration=iteration;audit.issue_width=current_issue_width;
  if(iteration){for(const auto net:net_order)if(pending.count(net))ripup(trees[net],owners,result.tasks,result.metrics,edge_executor?&wide.task_edges:nullptr);owners.refresh_all();}
  std::map<std::uint32_t,std::size_t> cursors;for(const auto net:pending)cursors[net]=0;
  while(true){
   std::vector<Task> wave;std::vector<std::vector<SearchSeed>> seeds;
   for(const auto net:net_order){if(!pending.count(net))continue;auto& tree=trees[net];auto& cursor=cursors[net];if(cursor<tree.tasks.size()){Task task=result.tasks[tree.tasks[cursor++]].task;task.epoch=iteration;wave.push_back(task);seeds.push_back(tree_seeds(tree,task.criticality_q,config.route_tree_timing_weight_q));}}
   if(wave.empty())break;
   ++audit.waves;audit.launched+=wave.size();result.metrics.searches+=wave.size();
   const std::uint32_t wave_issue_width=adaptive&&config.adaptive_issue_tail_tasks&&
    wave.size()<=config.adaptive_issue_tail_tasks?config.adaptive_issue_width_min:current_issue_width;
   audit.issue_width=std::min(audit.issue_width,wave_issue_width);
   for(std::size_t begin=0;begin<wave.size();begin+=wave_issue_width){
    const std::size_t end=std::min<std::size_t>(wave.size(),begin+wave_issue_width);
    std::vector<Task> batch_tasks(wave.begin()+begin,wave.begin()+end);
    std::vector<std::vector<SearchSeed>> batch_seeds(seeds.begin()+begin,seeds.begin()+end);
    EdgeBatchResult extended;
    KernelBatchResult batch;
    if(edge_executor){extended=(*edge_executor)(nodes,edges,result.resources,batch_tasks,batch_seeds,true,costs);batch=std::move(extended.batch);
     if(extended.edge_paths.size()!=batch.candidates.size())throw std::runtime_error("candidate edge sidecar count mismatch");
    }else batch=executor(nodes,edges,result.resources,batch_tasks,batch_seeds,true,costs);
    add_telemetry(audit.telemetry,batch.telemetry);add_telemetry(out.telemetry,batch.telemetry);
    result.metrics.expanded+=batch.search_metrics.expanded;result.metrics.edge_visits+=batch.search_metrics.edge_visits;
    std::map<std::uint32_t,const KernelCandidate*> by_id;
    std::map<std::uint32_t,const std::vector<std::uint32_t>*> by_edges;
    for(std::size_t j=0;j<batch.candidates.size();++j){const auto& candidate=batch.candidates[j];
     if(!by_id.emplace(candidate.task.id,&candidate).second)throw std::runtime_error("duplicate candidate task ID");
     if(edge_executor)by_edges[candidate.task.id]=&extended.edge_paths[j];}
    for(const auto& task:batch_tasks){
     const auto found=by_id.find(task.id);auto& tree=trees[task.net_id];
     const auto index=*std::find_if(tree.tasks.begin(),tree.tasks.end(),[&](auto i){return result.tasks[i].task.id==task.id;});
     RoutedTask& routed=result.tasks[index];routed.task.epoch=iteration;
     if(found==by_id.end()||found->second->search_status!=1||found->second->commit_status!=4){++audit.failed;++log.failed_connections;continue;}
     if(found->second->task.net_id!=task.net_id || found->second->task.sink!=task.sink || found->second->task.source!=task.source)throw std::runtime_error("candidate task identity mismatch");
     if(policy && !policy->path_allowed(task,found->second->attachment,found->second->path,*by_edges.at(task.id)))throw std::runtime_error("controller rejected forbidden candidate branch");
     accept_path(tree,owners,routed,found->second->attachment,found->second->path,nodes,edges,
      edge_executor?by_edges.at(task.id):nullptr,edge_executor?&wide.task_edges[index]:nullptr);++audit.committed;
    }
    owners.refresh_all();
   }
  }
  const std::uint32_t over=static_cast<std::uint32_t>(std::count_if(result.resources.begin(),result.resources.end(),[](const auto& r){return r.occupancy>r.capacity;}));
  log.overused_resources=over;audit.overused_resources=over;audit.resource_hash=hash_resources(result.resources,costs);audit.route_hash=hash_routes(result.tasks,edge_executor?&wide.task_edges:nullptr);
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
  if(over<best_overuse){best_overuse=over;stagnant_iterations=0;}else ++stagnant_iterations;
  if(adaptive&&stagnant_iterations>=config.adaptive_issue_stagnation_iterations&&
     current_issue_width>config.adaptive_issue_width_min){
   current_issue_width=std::max(config.adaptive_issue_width_min,(current_issue_width+1U)/2U);
   stagnant_iterations=0;best_overuse=over;
  }
  present=grow_present(present,config.present_multiplier_q);
  update_wide_costs(result.resources,costs,present,config.history_increment_q,policy.get());
  std::set<std::uint32_t> next;if(force_timing_reroute)next.insert(net_order.begin(),net_order.end());for(const auto& task:result.tasks)if(!task.routed)next.insert(task.task.net_id);
  for(std::size_t node=0;node<result.resources.size();++node)if(result.resources[node].occupancy>result.resources[node].capacity)for(const auto net:owners.at(node))next.insert(net);
  pending.swap(next);
 }
 for(const auto& item:trees){const auto& tree=item.second;NetRouteTree snapshot{tree.net_id,tree.source,{},{}};for(const auto& edge:tree.parent){snapshot.nodes.push_back(edge.first);if(edge.second!=INVALID_RESOURCE)snapshot.edges.push_back({edge.second,edge.first});}std::sort(snapshot.edges.begin(),snapshot.edges.end(),[](const auto& a,const auto& b){return std::tie(a.parent,a.child)<std::tie(b.parent,b.child);});result.route_trees.push_back(std::move(snapshot));}
 if(edge_executor){for(const auto& item:trees)for(const auto& e:item.second.parent_edge)wide.tree_edges.push_back({item.first,item.second.parent.at(e.first),e.first,e.second});
  std::sort(wide.tree_edges.begin(),wide.tree_edges.end(),[](const auto& a,const auto& b){return std::tie(a.net_id,a.parent,a.child,a.edge)<std::tie(b.net_id,b.parent,b.child,b.edge);});}
 if(policy){for(std::size_t n=0;n<nodes.size();++n)if(policy->frozen(n)){
   const auto& a=initial_resources[n];const auto& b=result.resources[n];
   if(a.occupancy!=b.occupancy || a.owner!=b.owner || a.version!=b.version || a.capacity!=b.capacity ||
      costs[n].present_q!=a.present_cost_q || costs[n].history_q!=a.history_cost_q)throw std::logic_error("protected authority changed during routing");}}
 result.legal=result.route_success&&validate_pathfinder_result(nodes,edges,initial_resources,result)&&(!edge_executor||validate_wide_edge_result(nodes,edges,wide));
 return wide;
}

WidePathfinderResult route_wide_pathfinder(const std::vector<Node>& nodes,const std::vector<Edge>& edges,
 const std::vector<Resource>& resources,const std::vector<Task>& tasks,const WideBatchExecutor& executor,
 const PathfinderConfig& config,std::uint32_t issue,const TimingAnalyzer& timing) {
 return route_wide_impl(nodes,edges,resources,tasks,executor,config,issue,timing,nullptr,{},{});
}
WidePathfinderResult route_wide_pathfinder_edges(const std::vector<Node>& nodes,const std::vector<Edge>& edges,
 const std::vector<Resource>& resources,const std::vector<Task>& tasks,const EdgeBatchExecutor& executor,
 const PathfinderConfig& config,std::uint32_t issue,const EdgeTimingAnalyzer& timing,RoutingPolicyPtr policy) {
 return route_wide_impl(nodes,edges,resources,tasks,{},config,issue,{},&executor,timing,std::move(policy));
}
bool validate_wide_edge_result(const std::vector<Node>& nodes,const std::vector<Edge>& edges,const WidePathfinderResult& wide) {
 const auto& result=wide.result.routing;
 if(!wide.edge_identity || wide.task_edges.size()!=result.tasks.size())return false;
 std::map<std::pair<std::uint32_t,std::uint32_t>,std::pair<std::uint32_t,std::uint32_t>> parents;
 for(const auto& row:wide.tree_edges){
  if(!valid_edge_path(nodes,edges,row.parent,{row.child},{row.edge}) ||
     !parents.emplace(std::make_pair(row.net_id,row.child),std::make_pair(row.parent,row.edge)).second)return false;
 }
 std::size_t count=0;
 for(const auto& tree:result.route_trees)for(const auto& e:tree.edges){++count;auto it=parents.find({tree.net_id,e.child});if(it==parents.end()||it->second.first!=e.parent)return false;}
 if(count!=parents.size())return false;
 for(std::size_t i=0;i<result.tasks.size();++i){const auto& routed=result.tasks[i];const auto& trace=wide.task_edges[i];
  if(!routed.routed){if(!trace.empty())return false;continue;}
  if(!valid_edge_path(nodes,edges,routed.task.source,routed.path,trace))return false;
  auto parent=routed.task.source;
  for(std::size_t j=0;j<trace.size();++j){auto it=parents.find({routed.task.net_id,routed.path[j]});
   if(it==parents.end() || it->second!=std::make_pair(parent,trace[j]))return false;
   parent=routed.path[j];}
 }
 return true;
}

} // namespace dieroute
