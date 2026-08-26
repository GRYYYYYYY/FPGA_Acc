#include "pathfinder.hpp"

#include <algorithm>
#include <limits>
#include <map>
#include <queue>
#include <set>
#include <stdexcept>
#include <tuple>

namespace persistroute {
namespace {

std::uint16_t saturate_u16(std::uint64_t value) {
 return static_cast<std::uint16_t>(std::min<std::uint64_t>(value, 65535U));
}

std::uint32_t saturate_u32(std::uint64_t value) {
 return static_cast<std::uint32_t>(std::min<std::uint64_t>(value, 0xffffffffULL));
}

struct TreeState {
 std::uint32_t net_id = INVALID_RESOURCE;
 std::uint32_t source = INVALID_RESOURCE;
 std::map<std::uint32_t, std::uint32_t> parent;
 std::vector<std::size_t> task_indices;
};

struct QueueEntry {
 std::uint32_t cost;
 std::uint32_t hops;
 std::uint32_t node;
 std::uint32_t predecessor;
};

struct QueueGreater {
 bool operator()(const QueueEntry& lhs, const QueueEntry& rhs) const {
  return std::tie(lhs.cost, lhs.hops, lhs.node, lhs.predecessor) >
         std::tie(rhs.cost, rhs.hops, rhs.node, rhs.predecessor);
 }
};

struct SearchOutput {
 bool found = false;
 std::uint64_t expanded = 0;
 std::uint64_t edge_visits = 0;
 std::vector<std::uint32_t> full_path;
 std::vector<std::uint32_t> branch;
 std::uint32_t attachment = INVALID_RESOURCE;
};

class OwnershipState {
public:
 OwnershipState(const std::vector<Resource>& initial, std::vector<Resource>& resources)
     : initial_(initial), resources_(resources), dynamic_(initial.size()) {}

 bool owns(std::uint32_t resource, std::uint32_t net_id) const {
  return dynamic_[resource].count(net_id) != 0 ||
         (initial_[resource].occupancy != 0 && initial_[resource].owner == net_id);
 }

 void add(std::uint32_t resource, std::uint32_t net_id) {
  if (dynamic_[resource].insert(net_id).second) refresh(resource);
 }

 void remove(std::uint32_t resource, std::uint32_t net_id) {
  if (dynamic_[resource].erase(net_id) != 0) refresh(resource);
 }

 const std::set<std::uint32_t>& dynamic_owners(std::uint32_t resource) const {
  return dynamic_[resource];
 }

private:
 void refresh(std::uint32_t resource) {
  Resource& state = resources_[resource];
  const Resource& base = initial_[resource];
  std::uint32_t occupancy = base.occupancy;
  std::set<std::uint32_t> known = dynamic_[resource];
  if (base.occupancy != 0 && base.owner != INVALID_RESOURCE) known.insert(base.owner);
  for (const auto net_id : dynamic_[resource]) {
   if (!(base.occupancy != 0 && base.owner == net_id)) ++occupancy;
  }
  const std::uint16_t next_occupancy = saturate_u16(occupancy);
  const std::uint32_t next_owner = next_occupancy == 1 && known.size() == 1
      ? *known.begin() : INVALID_RESOURCE;
  if (state.occupancy != next_occupancy || state.owner != next_owner) {
   state.occupancy = next_occupancy;
   state.owner = next_owner;
   ++state.version;
  }
 }

 const std::vector<Resource>& initial_;
 std::vector<Resource>& resources_;
 std::vector<std::set<std::uint32_t>> dynamic_;
};

std::map<std::uint32_t, std::uint32_t> tree_depths(const TreeState& tree) {
 std::map<std::uint32_t, std::uint32_t> depths;
 depths[tree.source] = 0;
 for (const auto& item : tree.parent) {
  if (item.first == tree.source) continue;
  std::uint32_t node = item.first;
  std::vector<std::uint32_t> chain;
  while (depths.count(node) == 0) {
   const auto found = tree.parent.find(node);
   if (found == tree.parent.end() || found->second == INVALID_RESOURCE ||
       chain.size() > tree.parent.size()) {
    throw std::logic_error("invalid persistent route tree");
   }
   chain.push_back(node);
   node = found->second;
  }
  std::uint32_t depth = depths[node];
  for (auto it = chain.rbegin(); it != chain.rend(); ++it) depths[*it] = ++depth;
 }
 return depths;
}

SearchOutput search_connection(
 const std::vector<Node>& nodes,
 const std::vector<Edge>& edges,
 const std::vector<Resource>& resources,
 const OwnershipState& ownership,
 const TreeState& tree,
 const Task& task) {
 const std::size_t count = nodes.size();
 std::vector<std::uint32_t> distance(count, 0xffffffffU);
 std::vector<std::uint32_t> hops(count, 0xffffffffU);
 std::vector<std::uint32_t> predecessor(count, INVALID_RESOURCE);
 std::vector<std::uint8_t> closed(count, 0);
 std::priority_queue<QueueEntry, std::vector<QueueEntry>, QueueGreater> queue;
 const auto depths = tree_depths(tree);
 for (const auto& seed : depths) {
  if (seed.second > task.max_hops) continue;
  distance[seed.first] = 0;
  hops[seed.first] = seed.second;
  queue.push({0, seed.second, seed.first, INVALID_RESOURCE});
 }

 SearchOutput output;
 while (!queue.empty()) {
  const QueueEntry current = queue.top();
  queue.pop();
  if (closed[current.node] || current.cost != distance[current.node] ||
      current.hops != hops[current.node]) continue;
  closed[current.node] = 1;
  ++output.expanded;
  if (current.node == task.sink) {
   output.found = true;
   break;
  }
  if (current.hops >= task.max_hops) continue;
  const Node node = nodes[current.node];
  for (std::uint32_t j = 0; j < node.edge_count; ++j) {
   const std::uint32_t edge_id = node.edge_begin + j;
   if (edge_id >= edges.size()) throw std::invalid_argument("node edge range exceeds edge array");
   const Edge edge = edges[edge_id];
   if (edge.dst >= count) throw std::invalid_argument("edge destination exceeds node array");
   if (closed[edge.dst]) continue;
   ++output.edge_visits;
   const Resource& state = resources[edge.dst];
   const bool same_net = ownership.owns(edge.dst, task.net_id);
   const std::uint32_t projected = static_cast<std::uint32_t>(state.occupancy) + (same_net ? 0U : 1U);
   const std::uint32_t overuse = projected > state.capacity ? projected - state.capacity : 0U;
   const std::uint64_t congestion = same_net ? 0ULL :
       static_cast<std::uint64_t>(state.history_cost_q) +
       static_cast<std::uint64_t>(state.present_cost_q) * overuse;
   const std::uint64_t timing = static_cast<std::uint64_t>(edge.delay_q) * task.criticality_q / 65535U;
   const std::uint32_t candidate = saturate_u32(
       static_cast<std::uint64_t>(current.cost) + edge.base_cost_q + congestion + timing);
   const std::uint32_t candidate_hops = current.hops + 1;
   const auto candidate_key = std::make_tuple(candidate, candidate_hops, current.node);
   const auto old_key = std::make_tuple(distance[edge.dst], hops[edge.dst], predecessor[edge.dst]);
   if (candidate_key < old_key) {
    distance[edge.dst] = candidate;
    hops[edge.dst] = candidate_hops;
    predecessor[edge.dst] = current.node;
    queue.push({candidate, candidate_hops, edge.dst, current.node});
   }
  }
 }
 if (!output.found) return output;

 std::vector<std::uint32_t> reverse_branch;
 std::uint32_t cursor = task.sink;
 while (predecessor[cursor] != INVALID_RESOURCE) {
  reverse_branch.push_back(cursor);
  cursor = predecessor[cursor];
 }
 output.attachment = cursor;
 output.branch.assign(reverse_branch.rbegin(), reverse_branch.rend());

 std::vector<std::uint32_t> reverse_prefix;
 cursor = output.attachment;
 while (cursor != tree.source) {
  reverse_prefix.push_back(cursor);
  const auto found = tree.parent.find(cursor);
  if (found == tree.parent.end() || found->second == INVALID_RESOURCE) {
   throw std::logic_error("search attached to a broken route tree");
  }
  cursor = found->second;
 }
 output.full_path.assign(reverse_prefix.rbegin(), reverse_prefix.rend());
 output.full_path.insert(output.full_path.end(), output.branch.begin(), output.branch.end());
 return output;
}

void add_branch(TreeState& tree, OwnershipState& ownership, const SearchOutput& search) {
 std::uint32_t parent = search.attachment;
 for (const auto child : search.branch) {
  const auto inserted = tree.parent.emplace(child, parent);
  if (inserted.second && child != tree.source) ownership.add(child, tree.net_id);
  parent = child;
 }
}

void ripup_tree(
 TreeState& tree,
 OwnershipState& ownership,
 std::vector<RoutedTask>& tasks,
 PathfinderMetrics& metrics) {
 if (tree.parent.size() > 1) ++metrics.ripups;
 for (const auto& item : tree.parent) {
  if (item.first != tree.source) ownership.remove(item.first, tree.net_id);
 }
 tree.parent.clear();
 tree.parent[tree.source] = INVALID_RESOURCE;
 for (const auto index : tree.task_indices) {
  if (tasks[index].routed) ++metrics.ripped_connections;
  tasks[index].routed = false;
  tasks[index].path.clear();
 }
}

std::uint32_t count_overused(const std::vector<Resource>& resources) {
 return static_cast<std::uint32_t>(std::count_if(resources.begin(), resources.end(),
     [](const Resource& state) { return state.occupancy > state.capacity; }));
}

void update_costs(
 std::vector<Resource>& resources,
 std::uint16_t present_factor,
 std::uint16_t history_increment) {
 for (auto& state : resources) {
  const std::uint32_t overuse = state.occupancy > state.capacity
      ? state.occupancy - state.capacity : 0U;
  const std::uint16_t next_history = saturate_u16(
      static_cast<std::uint64_t>(state.history_cost_q) +
      static_cast<std::uint64_t>(history_increment) * overuse);
  if (state.present_cost_q != present_factor || state.history_cost_q != next_history) {
   state.present_cost_q = present_factor;
   state.history_cost_q = next_history;
   ++state.version;
  }
 }
}

void validate_inputs(
 const std::vector<Node>& nodes,
 const std::vector<Edge>& edges,
 const std::vector<Resource>& resources,
 const std::vector<Task>& tasks,
 const PathfinderConfig& config) {
 if (nodes.empty() || nodes.size() != resources.size())
  throw std::invalid_argument("node/resource arrays must be non-empty and equally sized");
 if (config.max_iterations == 0 || config.min_timing_iterations == 0 ||
     config.min_timing_iterations > config.max_iterations || config.present_multiplier_q == 0)
  throw std::invalid_argument("PathFinder iteration and multiplier values must be positive");
 for (std::size_t i = 0; i < nodes.size(); ++i) {
  if (resources[i].capacity == 0) throw std::invalid_argument("resource capacity must be positive");
  if (static_cast<std::uint64_t>(nodes[i].edge_begin) + nodes[i].edge_count > edges.size())
   throw std::invalid_argument("node edge range exceeds edge array");
 }
 for (const auto& edge : edges)
  if (edge.dst >= nodes.size()) throw std::invalid_argument("edge destination exceeds node array");
 std::set<std::uint32_t> ids;
 std::map<std::uint32_t, std::uint32_t> sources;
 for (const auto& task : tasks) {
  if (!ids.insert(task.id).second) throw std::invalid_argument("task IDs must be unique");
  if (task.source >= nodes.size() || task.sink >= nodes.size())
   throw std::invalid_argument("task endpoint exceeds node array");
  const auto inserted = sources.emplace(task.net_id, task.source);
  if (!inserted.second && inserted.first->second != task.source)
   throw std::invalid_argument("all connections in one net must share a source");
 }
}

bool has_edge(
 const std::vector<Node>& nodes,
 const std::vector<Edge>& edges,
 std::uint32_t source,
 std::uint32_t sink) {
 const Node node = nodes[source];
 for (std::uint32_t j = 0; j < node.edge_count; ++j)
  if (edges[node.edge_begin + j].dst == sink) return true;
 return false;
}

void update_timing_criticalities(
 std::uint32_t iteration,
 const std::vector<Node>& nodes,
 const std::vector<Edge>& edges,
 std::vector<RoutedTask>& tasks,
 const TimingAnalyzer& analyzer,
 std::vector<PathfinderTimingIteration>& log) {
 if (!analyzer) return;
 const TimingAnalysisResult analysis = analyzer(iteration, nodes, edges, tasks);
 if (analysis.connections.size() != tasks.size())
  throw std::runtime_error("timing analyzer must return exactly one update per connection");
 std::map<std::uint32_t, TimingConnectionUpdate> updates;
 for (const auto& update : analysis.connections)
  if (!updates.emplace(update.task_id, update).second)
   throw std::runtime_error("timing analyzer returned a duplicate task ID");
 PathfinderTimingIteration item{};
 item.iteration = iteration;
 item.min_criticality_q = 65535U;
 item.critical_path_delay_ps = analysis.critical_path_delay_ps;
 for (auto& routed : tasks) {
  const auto found = updates.find(routed.task.id);
  if (found == updates.end())
   throw std::runtime_error("timing analyzer omitted a task ID");
  if (routed.task.criticality_q != found->second.criticality_q) ++item.updated_connections;
  routed.task.criticality_q = found->second.criticality_q;
  item.min_criticality_q = std::min(item.min_criticality_q, routed.task.criticality_q);
  item.max_criticality_q = std::max(item.max_criticality_q, routed.task.criticality_q);
 }
 if (tasks.empty()) item.min_criticality_q = 0;
 log.push_back(item);
}

} // namespace

PathfinderResult route_pathfinder(
 const std::vector<Node>& nodes,
 const std::vector<Edge>& edges,
 const std::vector<Resource>& initial_resources,
 const std::vector<Task>& input_tasks,
 const PathfinderConfig& config,
 const TimingAnalyzer& timing_analyzer) {
 validate_inputs(nodes, edges, initial_resources, input_tasks, config);
 PathfinderResult result;
 result.resources = initial_resources;
 result.tasks.reserve(input_tasks.size());
 for (const auto& task : input_tasks) result.tasks.push_back({task, {}, false});
 OwnershipState ownership(initial_resources, result.resources);

 std::map<std::uint32_t, TreeState> trees;
 for (std::size_t i = 0; i < result.tasks.size(); ++i) {
  const Task& task = result.tasks[i].task;
  TreeState& tree = trees[task.net_id];
  tree.net_id = task.net_id;
  tree.source = task.source;
  tree.parent.emplace(task.source, INVALID_RESOURCE);
  tree.task_indices.push_back(i);
 }
 for (auto& item : trees) {
  auto& indices = item.second.task_indices;
  std::sort(indices.begin(), indices.end(), [&](std::size_t lhs, std::size_t rhs) {
   const Task& a = result.tasks[lhs].task;
   const Task& b = result.tasks[rhs].task;
   return std::tie(a.priority, a.id) < std::tie(b.priority, b.id);
  });
 }
 std::vector<std::uint32_t> net_order;
 net_order.reserve(trees.size());
 for (const auto& item : trees) net_order.push_back(item.first);
 std::sort(net_order.begin(), net_order.end(), [&](std::uint32_t lhs, std::uint32_t rhs) {
  const Task& a = result.tasks[trees.at(lhs).task_indices.front()].task;
  const Task& b = result.tasks[trees.at(rhs).task_indices.front()].task;
  return std::tie(a.priority, a.id, lhs) < std::tie(b.priority, b.id, rhs);
 });

 std::set<std::uint32_t> pending_nets;
 for (const auto& item : trees) pending_nets.insert(item.first);
 std::uint16_t present_factor = config.present_start_q;
 update_costs(result.resources, present_factor, 0);

 for (std::uint32_t iteration = 0; iteration < config.max_iterations; ++iteration) {
  result.metrics.iterations = iteration + 1;
  PathfinderIteration log{iteration, static_cast<std::uint32_t>(pending_nets.size()), 0, 0,
                          present_factor};
  if (iteration != 0) {
   for (const auto net_id : net_order)
    if (pending_nets.count(net_id) != 0)
     ripup_tree(trees.at(net_id), ownership, result.tasks, result.metrics);
  }
  for (const auto net_id : net_order) {
   if (pending_nets.count(net_id) == 0) continue;
   TreeState& tree = trees.at(net_id);
   for (const auto index : tree.task_indices) {
    RoutedTask& routed = result.tasks[index];
    routed.task.epoch = iteration;
    const SearchOutput search = search_connection(
        nodes, edges, result.resources, ownership, tree, routed.task);
    ++result.metrics.searches;
    result.metrics.expanded += search.expanded;
    result.metrics.edge_visits += search.edge_visits;
    if (!search.found) {
     ++log.failed_connections;
     continue;
    }
    add_branch(tree, ownership, search);
    routed.path = search.full_path;
    routed.routed = true;
   }
  }

  const std::uint32_t overused = count_overused(result.resources);
  result.metrics.overused_resources = overused;
  log.overused_resources = overused;
  result.iteration_log.push_back(log);
  update_timing_criticalities(iteration, nodes, edges, result.tasks,
                              timing_analyzer, result.timing_log);
  if (timing_analyzer) {
   for (auto& item : trees) {
    auto& indices = item.second.task_indices;
    std::sort(indices.begin(), indices.end(), [&](std::size_t lhs, std::size_t rhs) {
     const Task& a = result.tasks[lhs].task;
     const Task& b = result.tasks[rhs].task;
     return std::make_tuple(65535U - a.criticality_q, a.priority, a.id) <
            std::make_tuple(65535U - b.criticality_q, b.priority, b.id);
    });
   }
   std::sort(net_order.begin(), net_order.end(), [&](std::uint32_t lhs, std::uint32_t rhs) {
    const Task& a = result.tasks[trees.at(lhs).task_indices.front()].task;
    const Task& b = result.tasks[trees.at(rhs).task_indices.front()].task;
    return std::make_tuple(65535U - a.criticality_q, a.priority, a.id, lhs) <
           std::make_tuple(65535U - b.criticality_q, b.priority, b.id, rhs);
   });
  }
  const bool all_routed = std::all_of(result.tasks.begin(), result.tasks.end(),
      [](const RoutedTask& task) { return task.routed; });
  const bool force_timing_reroute = timing_analyzer &&
      iteration + 1 < config.min_timing_iterations;
  if (all_routed && overused == 0 && !force_timing_reroute) {
   result.route_success = true;
   break;
  }
  if (iteration + 1 == config.max_iterations) break;

  const std::uint64_t grown =
      (static_cast<std::uint64_t>(present_factor) * config.present_multiplier_q + 128U) / 256U;
  present_factor = std::max<std::uint16_t>(1, saturate_u16(grown));
  update_costs(result.resources, present_factor, config.history_increment_q);
  std::set<std::uint32_t> next_pending;
  if (force_timing_reroute)
   next_pending.insert(net_order.begin(), net_order.end());
  for (const auto& routed : result.tasks)
   if (!routed.routed) next_pending.insert(routed.task.net_id);
  for (std::uint32_t resource = 0; resource < result.resources.size(); ++resource) {
   if (result.resources[resource].occupancy <= result.resources[resource].capacity) continue;
   for (const auto net_id : ownership.dynamic_owners(resource)) next_pending.insert(net_id);
  }
  pending_nets.swap(next_pending);
 }

 for (const auto& item : trees) {
  const TreeState& tree = item.second;
  NetRouteTree snapshot{tree.net_id, tree.source, {}, {}};
  snapshot.nodes.reserve(tree.parent.size());
  for (const auto& parent : tree.parent) {
   snapshot.nodes.push_back(parent.first);
   if (parent.second != INVALID_RESOURCE) snapshot.edges.push_back({parent.second, parent.first});
  }
  std::sort(snapshot.edges.begin(), snapshot.edges.end(), [](const auto& a, const auto& b) {
   return std::tie(a.parent, a.child) < std::tie(b.parent, b.child);
  });
  result.route_trees.push_back(std::move(snapshot));
 }
 result.legal = result.route_success &&
     validate_pathfinder_result(nodes, edges, initial_resources, result);
 return result;
}

bool validate_pathfinder_result(
 const std::vector<Node>& nodes,
 const std::vector<Edge>& edges,
 const std::vector<Resource>& initial_resources,
 const PathfinderResult& result) {
 if (nodes.size() != initial_resources.size() || result.resources.size() != nodes.size()) return false;
 std::vector<std::set<std::uint32_t>> routed_owners(nodes.size());
 std::map<std::uint32_t, std::set<std::uint32_t>> expected_tree_nodes;
 std::map<std::uint32_t, std::map<std::uint32_t, std::uint32_t>> expected_tree_parent;
 for (const auto& routed : result.tasks) {
  if (!routed.routed) return false;
  std::uint32_t previous = routed.task.source;
  expected_tree_nodes[routed.task.net_id].insert(previous);
  if (routed.path.empty() && routed.task.source != routed.task.sink) return false;
  for (const auto resource : routed.path) {
   if (resource >= nodes.size() || !has_edge(nodes, edges, previous, resource)) return false;
   routed_owners[resource].insert(routed.task.net_id);
   expected_tree_nodes[routed.task.net_id].insert(resource);
   const auto inserted=expected_tree_parent[routed.task.net_id].emplace(resource,previous);
   if(!inserted.second&&inserted.first->second!=previous)return false;
   previous = resource;
  }
  if (previous != routed.task.sink) return false;
 }
 std::set<std::uint32_t> seen_trees;
 for(const auto& tree:result.route_trees){
  if(!seen_trees.insert(tree.net_id).second)return false;
  const auto expected=expected_tree_nodes.find(tree.net_id);
  if(expected==expected_tree_nodes.end()||expected->second.count(tree.source)==0)return false;
  if(std::set<std::uint32_t>(tree.nodes.begin(),tree.nodes.end())!=expected->second||
     tree.nodes.size()!=expected->second.size())return false;
  std::map<std::uint32_t,std::uint32_t> observed_parent;
  for(const auto& edge:tree.edges){
   if(!has_edge(nodes,edges,edge.parent,edge.child)||
      !observed_parent.emplace(edge.child,edge.parent).second)return false;
  }
  if(observed_parent!=expected_tree_parent[tree.net_id])return false;
 }
 if(seen_trees.size()!=expected_tree_nodes.size())return false;
 for (std::size_t i = 0; i < nodes.size(); ++i) {
  std::uint32_t expected = initial_resources[i].occupancy;
  std::set<std::uint32_t> known_owners=routed_owners[i];
  if(initial_resources[i].occupancy!=0&&initial_resources[i].owner!=INVALID_RESOURCE)
   known_owners.insert(initial_resources[i].owner);
  for (const auto net_id : routed_owners[i]) {
   if (!(initial_resources[i].occupancy != 0 && initial_resources[i].owner == net_id)) ++expected;
  }
  const std::uint32_t expected_owner=expected==1&&known_owners.size()==1
      ?*known_owners.begin():INVALID_RESOURCE;
  if (expected > 65535U || result.resources[i].occupancy != expected ||
      result.resources[i].occupancy > result.resources[i].capacity||
      result.resources[i].owner!=expected_owner) return false;
 }
 return true;
}

} // namespace persistroute
