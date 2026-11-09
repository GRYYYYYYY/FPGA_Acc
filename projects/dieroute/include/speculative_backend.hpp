#pragma once
#include "rr_backend.hpp"
#include <memory>

namespace dieroute {
struct BoundaryShadow {
    std::uint16_t capacity = 0, occupancy = 0;
    std::uint32_t version = 0;
    std::uint64_t present_q = 0, history_q = 0;
    bool valid = false;
};
struct ShadowMessage {
    // Logical payload budget: resource:u32, owner/target:u16 each,
    // version:u32, capacity/occupancy:u16 each, present/history:u64 each = 32B.
    // CPU struct padding and the local validity flag are not a wire encoding.
    std::uint32_t resource;
    std::uint16_t owner_die;
    BoundaryShadow value;
};
struct ShadowMetrics {
    std::uint64_t published = 0, payload_bytes = 0, stale_dropped = 0;
};

// Capacity/version/cost only: shadow records never contain a writable net owner.
// This reference broadcasts boundary summaries to every non-owner die. It does
// not model a hardware network, HBM latency, or bandwidth overlap.
class BoundaryShadows {
public:
    BoundaryShadows(std::vector<std::uint16_t> owners, std::vector<bool> boundary);
    void stage(const std::vector<persistroute::Resource>&, const std::vector<WideCost>*);
    void publish();
    bool receive(std::uint16_t target_die, const ShadowMessage&);
    RRStateView view(std::uint16_t observer_die, const std::vector<persistroute::Resource>&,
                    const std::vector<WideCost>*) const;
    bool remote_boundary(std::uint16_t die, std::uint32_t node) const;
    const ShadowMetrics& metrics() const { return metrics_; }
    std::size_t summary_records() const {return latest_.size()*(replicas_.size()+1);}
    std::size_t boundary_records() const {return boundary_nodes_.size();}
private:
    std::vector<std::uint16_t> owners_;
    std::vector<bool> boundary_;
    std::vector<std::uint32_t> boundary_nodes_;
    std::unordered_map<std::uint32_t,std::size_t> boundary_index_;
    std::vector<BoundaryShadow> latest_;
    std::vector<std::vector<BoundaryShadow>> replicas_;
    ShadowMetrics metrics_;
};

enum class ProposalCommit { committed, stale, unreachable, capacity, invalid, overflow };
// For an electrically checked RRProposal, validate the whole read set and every
// capacity/version write before the first state mutation. A stale overflow is
// replayable; a current-snapshot overflow is rejected without writes.
ProposalCommit commit_proposal(std::vector<persistroute::Resource>&, const RRProposal&, bool allow_overuse);
ProposalCommit commit_proposal(std::vector<persistroute::Resource>&, const RRProposal&, bool,
    const std::vector<persistroute::Node>&, const std::vector<persistroute::Edge>&,
    const RoutingPolicy& = {});

struct SpeculativeMetrics {
    std::uint64_t windows = 0, proposals = 0, replays = 0, conflicts = 0;
    std::uint64_t read_entries = 0, remote_shadow_reads = 0;
    std::uint32_t maximum_window_tasks = 0;
};
struct TransactionTrace {
    std::uint64_t window, initial_read_hash, replay_read_hash, path_hash;
    std::uint32_t task, epoch, priority, initial_reads, final_reads;
    ProposalCommit initial_status, final_status;
    bool replayed = false;
};
class SpeculativeBackend {
public:
    SpeculativeBackend(const std::vector<persistroute::Node>&, const std::vector<persistroute::Edge>&,
                       std::vector<std::uint16_t> owners, std::vector<RRBox> boxes,
                       RRBackendConfig = {}, std::vector<std::uint16_t> membership = {},
                       std::vector<std::uint16_t> edge_die = {}, std::uint32_t workers = 4,
                       std::uint32_t shadow_sync_windows = 1, RoutingPolicyPtr policy = {});
    persistroute::KernelBatchResult execute(const std::vector<persistroute::Node>&,
        const std::vector<persistroute::Edge>&, std::vector<persistroute::Resource>&,
        const std::vector<persistroute::Task>&, const std::vector<std::vector<persistroute::SearchSeed>>&,
        bool allow_overuse, const std::vector<WideCost>* = nullptr);
    EdgeBatchResult execute_edges(const std::vector<persistroute::Node>&,
        const std::vector<persistroute::Edge>&, std::vector<persistroute::Resource>&,
        const std::vector<persistroute::Task>&, const std::vector<std::vector<persistroute::SearchSeed>>&,
        bool, const std::vector<WideCost>* = nullptr);
    const RRBackendMetrics& metrics() const { return work_; }
    const SpeculativeMetrics& speculative_metrics() const { return metrics_; }
    const ShadowMetrics& shadow_metrics() const { return shadows_.metrics(); }
    const std::vector<TransactionTrace>& trace() const { return trace_; }
private:
    EdgeBatchResult execute_impl(const std::vector<persistroute::Node>&,
        const std::vector<persistroute::Edge>&, std::vector<persistroute::Resource>&,
        const std::vector<persistroute::Task>&, const std::vector<std::vector<persistroute::SearchSeed>>&,
        bool, const std::vector<WideCost>*);
    bool edge_identity_ = false;
    RoutingPolicyPtr policy_;
    std::vector<std::uint16_t> owners_;
    BoundaryShadows shadows_;
    std::vector<std::unique_ptr<RRBackend>> workers_;
    std::uint32_t sync_windows_;
    RRBackendMetrics work_;
    SpeculativeMetrics metrics_;
    std::vector<TransactionTrace> trace_;
};
} // namespace dieroute
