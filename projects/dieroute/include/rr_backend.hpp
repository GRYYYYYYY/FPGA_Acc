#pragma once

#include "accelerated_pathfinder.hpp"
#include "wide_costs.hpp"
#include "routing_policy.hpp"
#include "sparse_search.hpp"
#include "rr_state_view.hpp"
#include <cstdint>
#include <vector>

namespace dieroute {
struct RRBox { std::uint16_t xlow, ylow, xhigh, yhigh; };
struct RRBackendConfig {
    bool hierarchical = true;
    std::uint32_t repair_attempts = 8;
    std::uint32_t geometry_weight = 64;
    bool downstream_cost = false;
    bool bound_downstream = false;
    bool vpr_style_cost = false;
    bool edge_identity = false;
};
// Integer cost reference shared by all searches, corridor scoring and tests.
// The optional form uses PR's Q8 history/present state as multiplicative factors;
// it does not reproduce VPR's complete RC, fanout or non-configurable-set model.
std::uint64_t rr_edge_cost(const persistroute::Edge&, const persistroute::Resource&,
                          const persistroute::Task&, bool owns, bool vpr_style,
                          const WideCost* wide_cost = nullptr);
struct RRBackendMetrics {
    std::uint64_t planned = 0, local_searches = 0, flat_searches = 0;
    std::uint64_t reserved_resources = 0, aborted_reservations = 0;
    std::uint64_t committed_corridors = 0, repairs = 0, fallbacks = 0;
    std::uint64_t committed_crossings = 0, overcapacity_reservations = 0;
    std::uint64_t structurally_pruned_portals = 0;
    std::uint64_t downstream_searches = 0, downstream_expanded = 0, downstream_edge_visits = 0;
    std::uint64_t downstream_cutoffs = 0;
};

struct RRProposal {
    persistroute::KernelCandidate candidate;
    persistroute::Metrics search_metrics{};
    persistroute::KernelBatchTelemetry telemetry{};
    RRBackendMetrics work{};
    bool corridor = false;
    std::uint64_t owner_changes = 0;
    std::uint64_t selected_reservations = 0;
    bool overflowed = false;
    bool requires_edge_identity = false;
    bool requires_policy = false;
    std::vector<std::uint32_t> edge_path;
};

// Serial golden executor. Reservations are candidate-local read journals keyed
// by physical RR ID, not a second authoritative occupancy array. PR owns the
// route trees and persistent state, including rip-up and same-net sharing.
// No claim of parallel hardware execution is made by this C++ implementation.
class RRBackend {
public:
    // Optional native sidecars must both be supplied: one <=8-die bit mask per
    // canonical electrical node, and one physical PIP die per CSR edge.
    // node_die selects the single authoritative owner, not physical membership.
    // Without sidecars, preserve the original single-layer VPR representation.
    RRBackend(const std::vector<persistroute::Node>& nodes,
              const std::vector<persistroute::Edge>& edges,
              std::vector<std::uint16_t> node_die, std::vector<RRBox> boxes,
              RRBackendConfig config = {},
              std::vector<std::uint16_t> node_membership = {},
              std::vector<std::uint16_t> edge_die = {}, RoutingPolicyPtr policy = {});
    persistroute::KernelBatchResult execute(
        const std::vector<persistroute::Node>& nodes, const std::vector<persistroute::Edge>& edges,
        std::vector<persistroute::Resource>& resources, const std::vector<persistroute::Task>& tasks,
        const std::vector<std::vector<persistroute::SearchSeed>>& seeds, bool allow_overuse,
        const std::vector<WideCost>* wide_costs = nullptr);
    EdgeBatchResult execute_edges(
        const std::vector<persistroute::Node>&, const std::vector<persistroute::Edge>&,
        std::vector<persistroute::Resource>&, const std::vector<persistroute::Task>&,
        const std::vector<std::vector<persistroute::SearchSeed>>&, bool,
        const std::vector<WideCost>* = nullptr);
    // Read-only speculative search. The journal includes every resource read
    // affecting selection, including rejected alternatives and failed searches.
    // One RRBackend instance per worker; no shared mutable worker counters.
    RRProposal propose(const std::vector<persistroute::Node>&,
                       const std::vector<persistroute::Edge>&,
                       const std::vector<persistroute::Resource>&,
                       const persistroute::Task&,
                       const std::vector<persistroute::SearchSeed>&, bool allow_overuse,
                       const std::vector<WideCost>* wide_costs = nullptr);
    RRProposal propose_view(const std::vector<persistroute::Node>&,
                       const std::vector<persistroute::Edge>&, const RRStateView&,
                       const persistroute::Task&, const std::vector<persistroute::SearchSeed>&,
                       bool allow_overuse);
    const RRBackendMetrics& metrics() const { return metrics_; }
    std::size_t search_workspace_bytes() const { return search_.retained_bytes()+downstream_.retained_bytes(); }
private:
    persistroute::KernelBatchResult execute_impl(
        const std::vector<persistroute::Node>&, const std::vector<persistroute::Edge>&,
        const RRStateView&, const std::vector<persistroute::Task>&,
        const std::vector<std::vector<persistroute::SearchSeed>>&, bool,
        std::vector<persistroute::Resource>*, RRProposal*,
        std::vector<std::vector<std::uint32_t>>*);
    // edge==UINT32_MAX is a zero-hop transition inside ONE electrical node.
    // It has no extra occupancy, delay, base cost or synthetic RR path entry.
    struct Portal {
        std::uint32_t source, edge, required_root, destination, id;
        std::uint16_t from_die, to_die;
    };
    std::vector<std::uint16_t> dies_;
    std::vector<std::uint16_t> membership_, edge_die_;
    std::vector<RRBox> boxes_;
    std::vector<Portal> portals_;
    std::vector<bool> source_roots_;
    struct Incoming { std::uint32_t source, edge; };
    std::vector<std::vector<Incoming>> incoming_;
    std::uint32_t die_count_ = 0;
    RRBackendConfig config_;
    RoutingPolicyPtr policy_;
    RRBackendMetrics metrics_;
    SparseSearch search_;
    SparseNodeTable<std::uint64_t> downstream_{UINT64_MAX};
};
} // namespace dieroute
