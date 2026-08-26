#include "accelerated_pathfinder.hpp"

#include <algorithm>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <tuple>

namespace persistroute {
namespace {

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
    config.present_multiplier_q==0)throw std::invalid_argument("invalid accelerated PathFinder sizes/config");
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

void ripup(TreeState& tree,Owners& owners,std::vector<RoutedTask>& tasks,PathfinderMetrics& metrics) {
 if(tree.parent.size()>1)++metrics.ripups;
 for(const auto& item:tree.parent)if(item.first!=tree.source)owners.remove(item.first,tree.net_id);
 tree.parent.clear();tree.parent[tree.source]=INVALID_RESOURCE;
 for(const auto index:tree.tasks){if(tasks[index].routed)++metrics.ripped_connections;tasks[index].routed=false;tasks[index].path.clear();}
}

} // namespace

AcceleratedPathfinderResult route_accelerated_pathfinder(
 const std::vector<Node>& nodes,const std::vector<Edge>& edges,
 const std::vector<Resource>& initial_resources,const std::vector<Task>& input_tasks,
 const KernelBatchExecutor& executor,const PathfinderConfig& config,std::uint32_t issue_width) {
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
  const bool all=std::all_of(result.tasks.begin(),result.tasks.end(),[](const auto& task){return task.routed;});
  if(all&&over==0){result.route_success=true;break;}if(iteration+1==config.max_iterations)break;
  const std::uint64_t grown=(static_cast<std::uint64_t>(present)*config.present_multiplier_q+128U)/256U;
  present=std::max<std::uint16_t>(1,sat16(grown));update_costs(result.resources,present,config.history_increment_q);
  std::set<std::uint32_t> next;for(const auto& task:result.tasks)if(!task.routed)next.insert(task.task.net_id);
  for(std::size_t node=0;node<result.resources.size();++node)if(result.resources[node].occupancy>result.resources[node].capacity)for(const auto net:owners.at(node))next.insert(net);
  pending.swap(next);
 }
 for(const auto& item:trees){const auto& tree=item.second;NetRouteTree snapshot{tree.net_id,tree.source,{},{}};for(const auto& edge:tree.parent){snapshot.nodes.push_back(edge.first);if(edge.second!=INVALID_RESOURCE)snapshot.edges.push_back({edge.second,edge.first});}std::sort(snapshot.edges.begin(),snapshot.edges.end(),[](const auto& a,const auto& b){return std::tie(a.parent,a.child)<std::tie(b.parent,b.child);});result.route_trees.push_back(std::move(snapshot));}
 result.legal=result.route_success&&validate_pathfinder_result(nodes,edges,initial_resources,result);
 return out;
}

} // namespace persistroute
