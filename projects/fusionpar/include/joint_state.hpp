#pragma once

#include "accelerated_pathfinder.hpp"

#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <vector>

namespace fusionpar::joint {
using Id = std::uint32_t;
constexpr Id invalid = 0xffffffffU;

// IDs in this in-memory v1 contract are dense vector indices. No binary ABI is
// implied. Pin IDs are logical packed-block pins, resolved independently per site.
struct Terminal { Id pin, node; bool source; };
struct Site {
    std::int32_t x = 0, y = 0, subtile = 0;
    Id type = 0;
    std::vector<Terminal> terminals;
};
struct Instance {
    Id type = 0;
    bool fixed = false;
    // Required explicit allow-list: includes region/clock/type eligibility.
    std::vector<Id> allowed_sites;
};
struct MacroMember { Id instance; std::int32_t dx, dy, dsubtile; };
struct Macro { Id anchor; std::vector<MacroMember> members; };
struct Connection {
    Id net, source_instance, source_pin, sink_instance, sink_pin;
    std::uint16_t max_hops = 65535;
    Id priority = 0;
};
struct Design {
    std::vector<persistroute::Node> nodes;
    std::vector<persistroute::Edge> edges;
    std::vector<Site> sites;
    std::vector<Instance> instances;
    std::vector<Macro> macros;
    std::vector<Connection> connections;
};
struct Placement { Id site = invalid; std::uint32_t version = 0; };
struct Route {
    Id source = invalid, sink = invalid;
    // Full root-to-sink path EXCLUDING source, as in the PR production ABI.
    std::vector<Id> path;
    std::uint32_t version = 0;
};
struct State {
    std::vector<Placement> placement;
    std::vector<std::uint32_t> site_versions;
    std::vector<Route> routes;
    std::vector<persistroute::Resource> resources;
    std::vector<std::uint16_t> criticalities;
    std::uint64_t revision = 0, timing_epoch = 0, timing_basis_revision = 0;
};
struct Move { Id instance, old_site, new_site; std::uint32_t observed_version; };
struct Proposal { std::uint64_t id = 0; std::vector<Move> moves; };
enum class Status {
    ready, committed, invalid_move, placement_illegal, sketch_rejected,
    route_failed, candidate_invalid, quality_rejected, stale_state,
    stale_timing, foreign_transaction, consumed, budget_exhausted
};
const char* status_name(Status);
struct Metrics {
    std::uint64_t snapshot_ns = 0, routing_ns = 0, validation_ns = 0;
    std::uint64_t prepare_ns = 0, commit_ns = 0, copied_payload_bytes = 0;
    std::uint64_t expanded = 0, edge_visits = 0;
    std::uint32_t affected_nets = 0, affected_connections = 0, route_iterations = 0;
    std::uint32_t touched_resources = 0;
    std::vector<Id> retained_connections;
    std::uint64_t kernel_searches = 0;
};
struct RoutingRequest {
    const Design& design;
    const std::vector<persistroute::Resource>& base_resources;
    const std::vector<persistroute::Task>& tasks;
    // Complete old root-to-sink branches whose endpoints are unchanged.
    // Synchronous lifetime; base_resources excludes ALL requested nets.
    const std::vector<persistroute::RoutedTask>* retained = nullptr;
};
enum class FeedbackKind { none, routing, native_delay, wire_growth };
struct FailureFeedback {
    FeedbackKind kind = FeedbackKind::none;
    // Ordered by the producer's deterministic failure/severity order.
    std::vector<Id> connection_ids, resource_ids;
};
const char* feedback_name(FeedbackKind);
struct RoutingReply {
    bool success = false;
    std::vector<persistroute::RoutedTask> tasks;
    std::uint64_t expanded = 0, edge_visits = 0;
    std::uint32_t iterations = 0;
    std::string detail;
    FailureFeedback feedback;
    std::uint64_t kernel_searches = 0;
};
using Router = std::function<RoutingReply(const RoutingRequest&)>;
using Sketch = std::function<bool(const Design&, const State&, const Proposal&)>;
// Must validate the candidate without mutating authoritative state. Native tool
// adapters may also archive candidate files here. False aborts the transaction.
using Validator = std::function<bool(const Design&, const State&, std::string&)>;
using Acceptance = std::function<bool(const Design&, const State&, const State&)>;

class Engine;
class Transaction {
public:
    Status status() const { return status_; }
    const std::string& detail() const { return detail_; }
    const Metrics& metrics() const { return metrics_; }
    const State* candidate() const { return candidate_.get(); }
    const Proposal& proposal() const { return proposal_; }
    const FailureFeedback& feedback() const { return feedback_; }
private:
    friend class Engine;
    std::shared_ptr<const int> origin_;
    std::shared_ptr<const State> base_;
    std::unique_ptr<State> candidate_;
    Proposal proposal_;
    Status status_ = Status::invalid_move;
    std::string detail_;
    Metrics metrics_;
    FailureFeedback feedback_;
    bool consumed_ = false;
};

// Single-threaded controller; prepare may retain many immutable snapshots.
// v1 conservatively validates the WHOLE state revision (not disjoint commits).
class Engine {
public:
    Engine(Design design, State initial, Router router, Validator validator = {});
    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;
    Engine(Engine&&) = delete;
    Engine& operator=(Engine&&) = delete;
    const Design& design() const { return design_; }
    const State& state() const { return *state_; }
    Transaction prepare(const Proposal&, const Sketch& = {}, const Acceptance& = {}, bool reroute_all = false,
                        bool retain_branches = false);
    // Explicit fixed-placement global routing epoch. Does not authorize an
    // empty/no-op placement proposal through the normal move interface.
    Transaction prepare_routing(const Acceptance& = {});
    Status commit(Transaction&);
    void timing_barrier(std::uint64_t observed_revision,
                        const std::vector<std::uint16_t>& criticalities);
private:
    Transaction prepare_impl(const Proposal&,const Sketch&,const Acceptance&,bool,bool,bool);
    Design design_;
    std::shared_ptr<const State> state_;
    Router router_;
    Validator validator_;
    std::shared_ptr<const int> identity_ = std::make_shared<const int>(0);
};

Router pr_cmodel_router(persistroute::PathfinderConfig config = {}, Id pe_count = 1,
                       Id issue_width = 1);
// Same PR kernels, FP controller with explicit retained trees. Empty retention
// provides the paired whole-net reconstruction control with identical ordering.
Router retained_cmodel_router(persistroute::PathfinderConfig config = {});
persistroute::KernelBatchExecutor guarded_cmodel_executor(const Design&,
    const std::vector<persistroute::Task>&, Id pe_count = 1);
bool validate_state(const Design&, const State&, std::string& error);
// Explicit input constructor: recomputes occupancy/owner from all route trees;
// it never repairs an imported state silently during validation or commit.
void initialize_accounting(const Design&, State&);
std::string semantic_digest(const State&); // deterministic diagnostic FNV, not SHA
std::uint64_t routed_wire_units(const Design&, const State&);
std::vector<Proposal> propose_moves(const Design&, const State&, std::size_t limit);
// Select legal alternative moves for an instance implicated by failed routing
// or native quality feedback. Remain within its failed displacement radius.
// Empty/stale/unrelated feedback does not authorize unrelated placement work.
std::vector<Proposal> propose_repairs(const Design&, const State&, const Proposal&,
                                    Status, const FailureFeedback&, std::size_t limit);

struct Attempt {
    std::uint64_t proposal_id = 0;
    std::uint32_t repair_index = 0;
    Status status = Status::invalid_move;
    Metrics metrics;
    std::string before, after, detail;
};
using Repair = std::function<std::vector<Proposal>(const Design&, const State&,
                                                 const Proposal&, Status)>;
struct ControllerResult { std::vector<Attempt> attempts; bool accepted = false; };
ControllerResult run_proposal(Engine&, const Proposal&, std::uint32_t repair_budget,
                             const Repair& = {}, const Sketch& = {}, const Acceptance& = {});
} // namespace fusionpar::joint
