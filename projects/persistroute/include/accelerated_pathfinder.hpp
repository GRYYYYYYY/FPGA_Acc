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

struct SearchSeed {
 std::uint32_t node = 0;
 std::uint32_t hops = 0;
 std::uint32_t cost_q = 0;
};

struct KernelBatchTelemetry {
 std::uint64_t h2d_bytes = 0;
 std::uint64_t d2h_bytes = 0;
 std::uint64_t search_ns = 0;
 std::uint64_t commit_ns = 0;
 std::uint32_t search_launches = 0;
 std::uint32_t commit_launches = 0;
};

struct KernelBatchResult {
 std::vector<KernelCandidate> candidates;
 Metrics search_metrics{};
 Metrics commit_metrics{};
 KernelBatchTelemetry telemetry{};
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
 std::uint32_t issue_width = 0;
 std::uint32_t waves = 0;
 std::uint32_t launched = 0;
 std::uint32_t committed = 0;
 std::uint32_t failed = 0;
 std::uint32_t overused_resources = 0;
 KernelBatchTelemetry telemetry{};
 std::uint64_t resource_hash = 0;
 std::uint64_t route_hash = 0;
};

struct AcceleratedPathfinderResult {
 PathfinderResult routing;
 std::vector<AcceleratedIteration> audit;
 std::uint32_t cleanup_attempted_nets = 0;
 std::uint32_t cleanup_accepted_nets = 0;
 std::uint32_t cleanup_attempted_branches = 0;
 std::uint32_t cleanup_accepted_branches = 0;
 std::uint64_t cleanup_wirelength_before = 0;
 std::uint64_t cleanup_wirelength_after = 0;
 std::uint64_t timing_ns = 0;
 std::uint64_t cleanup_ns = 0;
 KernelBatchTelemetry telemetry{};
};

struct SelectiveCleanupConfig {
 std::uint32_t passes = 0;
 std::uint16_t channel_length_cost_q = 0;
 std::uint32_t delay_tolerance_ppm = 0;
 std::uint32_t branch_budget_ppm = 0;
 std::uint32_t max_branches = 0;
 std::uint32_t time_budget_ms = 0;
 bool per_connection_delay_guard = true;
};

AcceleratedPathfinderResult route_accelerated_pathfinder(
 const std::vector<Node>& nodes,
 const std::vector<Edge>& edges,
 const std::vector<Resource>& initial_resources,
 const std::vector<Task>& tasks,
 const KernelBatchExecutor& executor,
 const PathfinderConfig& config = {},
 std::uint32_t issue_width = 4,
 const TimingAnalyzer& timing_analyzer = {},
 const SelectiveCleanupConfig& cleanup = {});

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
