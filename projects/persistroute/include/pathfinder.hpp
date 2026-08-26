#pragma once

#include "persistroute.hpp"

#include <cstdint>
#include <functional>
#include <vector>

namespace persistroute {

constexpr std::uint32_t INVALID_RESOURCE = 0xffffffffU;

struct PathfinderConfig {
 std::uint32_t max_iterations = 30;
 std::uint32_t min_timing_iterations = 1;
 std::uint16_t present_start_q = 256;
 std::uint16_t present_multiplier_q = 512; // Q8: 512 == 2.0
 std::uint16_t history_increment_q = 256;
};

struct RouteTreeEdge {
 std::uint32_t parent;
 std::uint32_t child;
};

struct NetRouteTree {
 std::uint32_t net_id;
 std::uint32_t source;
 std::vector<std::uint32_t> nodes;
 std::vector<RouteTreeEdge> edges;
};

struct RoutedTask {
 Task task;
 std::vector<std::uint32_t> path; // source excluded, matching the kernel ABI
 bool routed;
};

struct PathfinderIteration {
 std::uint32_t iteration;
 std::uint32_t routed_nets;
 std::uint32_t failed_connections;
 std::uint32_t overused_resources;
 std::uint32_t present_factor_q;
};

struct TimingConnectionUpdate {
 std::uint32_t task_id = 0;
 std::uint16_t criticality_q = 0;
 std::uint64_t delay_ps = 0;
 std::int64_t slack_ps = 0;
};

struct TimingAnalysisResult {
 std::uint64_t critical_path_delay_ps = 0;
 std::vector<TimingConnectionUpdate> connections;
};

using TimingAnalyzer = std::function<TimingAnalysisResult(
 std::uint32_t iteration,
 const std::vector<Node>& nodes,
 const std::vector<Edge>& edges,
 const std::vector<RoutedTask>& tasks)>;

struct PathfinderTimingIteration {
 std::uint32_t iteration = 0;
 std::uint32_t updated_connections = 0;
 std::uint16_t min_criticality_q = 0;
 std::uint16_t max_criticality_q = 0;
 std::uint64_t critical_path_delay_ps = 0;
};

struct PathfinderMetrics {
 std::uint64_t searches = 0;
 std::uint64_t expanded = 0;
 std::uint64_t edge_visits = 0;
 std::uint64_t ripups = 0;
 std::uint64_t ripped_connections = 0;
 std::uint32_t iterations = 0;
 std::uint32_t overused_resources = 0;
};

struct PathfinderResult {
 bool route_success = false;
 bool legal = false;
 PathfinderMetrics metrics;
 std::vector<Resource> resources;
 std::vector<RoutedTask> tasks;
 std::vector<NetRouteTree> route_trees;
 std::vector<PathfinderIteration> iteration_log;
 std::vector<PathfinderTimingIteration> timing_log;
};

PathfinderResult route_pathfinder(
 const std::vector<Node>& nodes,
 const std::vector<Edge>& edges,
 const std::vector<Resource>& initial_resources,
 const std::vector<Task>& tasks,
 const PathfinderConfig& config = {},
 const TimingAnalyzer& timing_analyzer = {});

bool validate_pathfinder_result(
 const std::vector<Node>& nodes,
 const std::vector<Edge>& edges,
 const std::vector<Resource>& initial_resources,
 const PathfinderResult& result);

} // namespace persistroute
