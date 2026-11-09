#pragma once
#include "accelerated_pathfinder.hpp"
#include "edge_routes.hpp"
#include "routing_policy.hpp"
#include <cstdint>
#include <vector>

namespace dieroute {
struct WideCost { std::uint64_t present_q, history_q; };
std::uint64_t grow_present(std::uint64_t present, std::uint16_t multiplier_q);
void update_wide_costs(std::vector<persistroute::Resource>& resources,
                       std::vector<WideCost>& costs, std::uint64_t present,
                       std::uint16_t history_step, const RoutingPolicy* policy = nullptr);
using WideBatchExecutor = std::function<persistroute::KernelBatchResult(
    const std::vector<persistroute::Node>&, const std::vector<persistroute::Edge>&,
    std::vector<persistroute::Resource>&, const std::vector<persistroute::Task>&,
    const std::vector<std::vector<persistroute::SearchSeed>>&, bool,
    const std::vector<WideCost>&)>;
using EdgeBatchExecutor = std::function<EdgeBatchResult(
    const std::vector<persistroute::Node>&, const std::vector<persistroute::Edge>&,
    std::vector<persistroute::Resource>&, const std::vector<persistroute::Task>&,
    const std::vector<std::vector<persistroute::SearchSeed>>&, bool,
    const std::vector<WideCost>&)>;
using EdgeTimingAnalyzer = std::function<persistroute::TimingAnalysisResult(
    std::uint32_t, const std::vector<persistroute::Node>&, const std::vector<persistroute::Edge>&,
    const std::vector<persistroute::RoutedTask>&, const std::vector<std::vector<std::uint32_t>>&)>;
struct WidePathfinderResult {
    persistroute::AcceleratedPathfinderResult result;
    std::vector<WideCost> costs;
    // The legacy result.routing.iteration_log present field is zero/reserved;
    // these u64 factors correspond one-to-one with those iteration records.
    std::vector<std::uint64_t> present_factors;
    bool edge_identity = false;
    std::vector<std::vector<std::uint32_t>> task_edges;
    std::vector<EdgeTreeEntry> tree_edges;
};
// Cost fields in result.routing.resources are zero/reserved. Authoritative
// costs live in costs and are hashed together with occupancy/owner/version.
WidePathfinderResult route_wide_pathfinder(
    const std::vector<persistroute::Node>& nodes, const std::vector<persistroute::Edge>& edges,
    const std::vector<persistroute::Resource>& initial_resources,
    const std::vector<persistroute::Task>& tasks, const WideBatchExecutor& executor,
    const persistroute::PathfinderConfig& config = {}, std::uint32_t issue_width = 4,
    const persistroute::TimingAnalyzer& timing_analyzer = {});
WidePathfinderResult route_wide_pathfinder_edges(
    const std::vector<persistroute::Node>& nodes, const std::vector<persistroute::Edge>& edges,
    const std::vector<persistroute::Resource>& initial_resources,
    const std::vector<persistroute::Task>& tasks, const EdgeBatchExecutor& executor,
    const persistroute::PathfinderConfig& config = {}, std::uint32_t issue_width = 4,
    const EdgeTimingAnalyzer& timing_analyzer = {}, RoutingPolicyPtr policy = {});
bool validate_wide_edge_result(const std::vector<persistroute::Node>&,
    const std::vector<persistroute::Edge>&,const WidePathfinderResult&);
} // namespace dieroute
