#pragma once

#include "pathfinder.hpp"

#include <functional>
#include <vector>

namespace persistroute {

struct KernelCandidate {
 Task task{};
 std::uint32_t attachment = INVALID_RESOURCE;
 std::vector<std::uint32_t> path;
 std::vector<ReadEntry> reads;
 std::uint16_t search_status = 0;
 std::uint16_t commit_status = 0;
};

struct SearchSeed {std::uint32_t node = 0;std::uint32_t hops = 0;};

struct KernelBatchResult {
 std::vector<KernelCandidate> candidates;
 Metrics search_metrics{};
 Metrics commit_metrics{};
};

using KernelBatchExecutor = std::function<KernelBatchResult(
 const std::vector<Node>&,
 const std::vector<Edge>&,
 std::vector<Resource>&,
 const std::vector<Task>&,
 const std::vector<std::vector<SearchSeed>>&,
 bool)>;

struct AcceleratedIteration {
 std::uint32_t iteration = 0;
 std::uint32_t waves = 0;
 std::uint32_t launched = 0;
 std::uint32_t committed = 0;
 std::uint32_t failed = 0;
 std::uint32_t overused_resources = 0;
 std::uint64_t resource_hash = 0;
 std::uint64_t route_hash = 0;
};

struct AcceleratedPathfinderResult {
 PathfinderResult routing;
 std::vector<AcceleratedIteration> audit;
};

AcceleratedPathfinderResult route_accelerated_pathfinder(
 const std::vector<Node>& nodes,
 const std::vector<Edge>& edges,
 const std::vector<Resource>& initial_resources,
 const std::vector<Task>& tasks,
 const KernelBatchExecutor& executor,
 const PathfinderConfig& config = {},
 std::uint32_t issue_width = 4);

KernelBatchResult execute_hbm_cmodel_batch(
 const std::vector<Node>& nodes,
 const std::vector<Edge>& edges,
 std::vector<Resource>& resources,
 const std::vector<Task>& tasks,
 const std::vector<std::vector<SearchSeed>>& seeds,
 bool allow_overuse,
 std::uint32_t pe_count = 4,
 std::uint32_t queue_depth = 0,
 std::uint32_t transaction_capacity = 0);

} // namespace persistroute
