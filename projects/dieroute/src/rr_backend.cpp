#include "rr_backend.hpp"

#include <algorithm>
#include <chrono>
#include <limits>
#include <numeric>
#include <queue>
#include <set>
#include <stdexcept>
#include <tuple>

namespace dieroute {
using namespace persistroute;
namespace {
constexpr auto none = std::numeric_limits<std::uint32_t>::max();
constexpr auto inf = std::numeric_limits<std::uint64_t>::max();

std::uint64_t gap(const RRBox& a, const RRBox& b) {
    const auto x = std::max({0, int(a.xlow) - int(b.xhigh), int(b.xlow) - int(a.xhigh)});
    const auto y = std::max({0, int(a.ylow) - int(b.yhigh), int(b.ylow) - int(a.yhigh)});
    return static_cast<std::uint64_t>(x + y);
}

std::uint64_t add_cost(std::uint64_t a, std::uint64_t b) {
    if (b >= inf - a) throw std::overflow_error("RR accumulated cost exceeds finite u64");
    return a + b;
}
} // namespace

std::uint64_t rr_edge_cost(const Edge& edge, const Resource& r, const Task& t, bool owns, bool vpr_style,
                          const WideCost* wide_cost) {
    __extension__ typedef unsigned __int128 U128;
    const auto present_q = wide_cost ? wide_cost->present_q : r.present_cost_q;
    const auto history_q = wide_cost ? wide_cost->history_q : r.history_cost_q;
    const auto projected = std::uint32_t(r.occupancy) + (owns ? 0U : 1U);
    const auto over = projected > r.capacity ? projected - r.capacity : 0U;
    if (vpr_style) {
        const U128 acc = owns ? 256 : U128(256) + history_q;
        const U128 present = owns ? 256 : U128(256) + U128(present_q) * over;
        const U128 base_acc = U128(edge.base_cost_q) * acc;
        // The full product can require 160 bits for u64 cost fields. Divide
        // first and bound the integer term before multiplying. The remainder
        // product uses at most 97 bits; neither term silently wraps or clamps.
        const auto quotient = base_acc / 65536U;
        if (quotient && present > U128(inf) / quotient)
            throw std::overflow_error("RR multiplicative congestion exceeds u64");
        const U128 congestion_wide = quotient * present + (base_acc % 65536U) * present / 65536U;
        if (congestion_wide > inf) throw std::overflow_error("RR congestion exceeds u64");
        const auto congestion = static_cast<std::uint64_t>(congestion_wide);
        const auto noncritical = 65535U - t.criticality_q;
        const auto weighted = (congestion / 65535U) * noncritical +
                              (congestion % 65535U) * noncritical / 65535U;
        return add_cost(weighted, std::uint64_t(edge.delay_q) * t.criticality_q / 65535U);
    }
    const U128 result = U128(edge.base_cost_q) + std::uint64_t(edge.delay_q) * t.criticality_q / 65535U +
        (owns ? U128(0) : U128(history_q) + U128(present_q) * over);
    if (result >= inf) throw std::overflow_error("RR additive cost exceeds finite u64");
    return static_cast<std::uint64_t>(result);
}

namespace {
class ResourceReader {
    const RRStateView& state_;
    std::vector<ReadEntry>* journal_;
    mutable SparseNodeTable<unsigned char> seen_;
public:
    ResourceReader(const RRStateView& state, std::vector<ReadEntry>* journal)
        : state_(state), journal_(journal) {}
    const Resource& operator[](std::uint32_t node) const {
        const auto& value = state_.resource(node);
        if (journal_ && !seen_.get(node)) {
            journal_->push_back({node, value.version}); seen_.touch(node) = 1;
        }
        return value;
    }
    const WideCost* cost(std::uint32_t node)const {
        (void)(*this)[node]; // Every cost read carries the observed resource version.
        return state_.cost(node);
    }
};
struct Segment {
    bool found = false;
    std::uint32_t attachment = none, hops = 0;
    std::vector<std::uint32_t> path, edge_path;
};

Segment search(const std::vector<Node>& nodes, const std::vector<Edge>& edges,
               const ResourceReader& resources, const std::vector<std::uint16_t>& membership,
               const std::vector<std::uint16_t>& edge_die, std::uint16_t local_die,
               const Task& task, const std::vector<SearchSeed>& seeds, std::uint32_t sink,
               bool local, bool overuse, bool vpr_style, const std::set<std::uint32_t>& blocked,
               persistroute::Metrics& metrics, const RoutingPolicy& policy,
               SparseSearch& workspace) {
    std::vector<SparseSeed> initial;
    for (const auto& s : seeds) {
        if (s.hops > task.max_hops || (local && !(membership[s.node] & (1U << local_die)))) continue;
        initial.push_back({s.node,s.hops,s.cost_q});
    }
    auto result=workspace.run(nodes.size(),initial,sink,task.max_hops,[&](std::uint32_t current,auto offer) {
        const auto& n = nodes[current];
        for (std::uint32_t i = 0; i < n.edge_count; ++i) {
            const auto& e = edges[n.edge_begin + i];
            if(!policy.edge_allowed(n.edge_begin+i) || !policy.node_allowed(e.dst,task.net_id))continue;
            if (local && edge_die[n.edge_begin + i] != local_die) continue;
            offer(e.dst,n.edge_begin+i,[&]()->std::optional<std::uint64_t> {
                if(blocked.count(e.dst))return {};
                const auto& state=resources[e.dst];const bool same=state.owner==task.net_id;
                if(!overuse && !same && state.occupancy>=state.capacity)return {};
                return rr_edge_cost(e,state,task,same,vpr_style,resources.cost(e.dst));
            });
        }
    },{},&metrics.expanded,&metrics.edge_visits);
    Segment out;out.found=result.status==SparseSearchStatus::found;out.hops=result.hops;
    out.attachment=result.attachment;out.path=std::move(result.path);out.edge_path=std::move(result.edges);return out;
}
} // namespace

RRBackend::RRBackend(const std::vector<Node>& nodes, const std::vector<Edge>& edges,
                     std::vector<std::uint16_t> dies, std::vector<RRBox> boxes,
                     RRBackendConfig config, std::vector<std::uint16_t> membership,
                     std::vector<std::uint16_t> edge_die, RoutingPolicyPtr policy)
    : dies_(std::move(dies)), membership_(std::move(membership)), edge_die_(std::move(edge_die)),
      boxes_(std::move(boxes)), config_(config),policy_(policy?std::move(policy):std::make_shared<RoutingPolicy>()) {
    policy_->validate(nodes.size(),edges.size());
    if(policy_->active()&&!config_.edge_identity)throw std::invalid_argument("routing policy requires explicit edge identity");
    if (nodes.empty() || nodes.size() != dies_.size() || nodes.size() != boxes_.size())
        throw std::invalid_argument("RR topology array size mismatch");
    die_count_ = 1 + *std::max_element(dies_.begin(), dies_.end());
    if (die_count_ > 8 || !config_.repair_attempts) throw std::invalid_argument("invalid die count/repair budget");
    const bool native_membership = !membership_.empty() || !edge_die_.empty();
    if (native_membership) {
        if (membership_.size() != nodes.size() || edge_die_.size() != edges.size())
            throw std::invalid_argument("membership/PIP die arrays must both cover the complete graph");
        for (std::size_t n = 0; n < nodes.size(); ++n) {
            if (!membership_[n] || (membership_[n] & ~255U) || !(membership_[n] & (1U << dies_[n])))
                throw std::invalid_argument("invalid native node membership/authoritative owner");
            for (unsigned d = 0; d < 8; ++d) if (membership_[n] & (1U << d))
                die_count_ = std::max(die_count_, d + 1);
        }
    } else {
        for (auto die : dies_) membership_.push_back(1U << die);
        edge_die_.assign(edges.size(), 65535);
    }
    std::vector<std::uint32_t> unique_parent(nodes.size(), none);
    incoming_.resize(nodes.size());
    constexpr auto ambiguous = none - 1;
    for (std::uint32_t n = 0; n < nodes.size(); ++n) {
        const auto& node = nodes[n]; const auto& b = boxes_[n];
        std::set<std::uint32_t> native_destinations;
        if (b.xlow > b.xhigh || b.ylow > b.yhigh || std::uint64_t(node.edge_begin) + node.edge_count > edges.size())
            throw std::invalid_argument("invalid RR CSR/geometry");
        for (std::uint32_t i = 0; i < node.edge_count; ++i) {
            const auto id = node.edge_begin + i;
            if (edges[id].dst >= nodes.size()) throw std::invalid_argument("RR edge out of bounds");
            if (native_membership) {
                if (!native_destinations.insert(edges[id].dst).second && !config_.edge_identity)
                    throw std::invalid_argument("parallel native PIPs require edge identity in route output");
                const auto d = edge_die_[id];
                if (d >= 8 || !(membership_[n] & (1U << d)) || !(membership_[edges[id].dst] & (1U << d)))
                    throw std::invalid_argument("PIP die is not a member of both electrical endpoints");
            }
            if(policy_->frozen(n) || policy_->frozen(edges[id].dst) || !policy_->edge_allowed(id))continue;
            incoming_[edges[id].dst].push_back({n, id});
            auto& pred = unique_parent[edges[id].dst];
            if (pred == none) pred = n;
            else if (pred != n) pred = ambiguous;
            if (!native_membership && dies_[n] != dies_[edges[id].dst])
                portals_.push_back({n, id, none, edges[id].dst, id, dies_[n], dies_[edges[id].dst]});
            else if(!native_membership) edge_die_[id] = dies_[n];
        }
    }
    if (native_membership) {
        for (std::uint32_t n = 0; n < nodes.size(); ++n)
            for (std::uint16_t a = 0; a < die_count_; ++a)
                for (std::uint16_t b = 0; b < die_count_; ++b)
                    if (a != b && !policy_->frozen(n) && (membership_[n] & (1U << a)) && (membership_[n] & (1U << b))) {
                        if (std::uint64_t(edges.size()) + portals_.size() >= none)
                            throw std::overflow_error("portal IDs exceed u32");
                        portals_.push_back({n, none, none, n,
                            static_cast<std::uint32_t>(edges.size() + portals_.size()), a, b});
                    }
    }
    source_roots_.resize(nodes.size());
    for (std::size_t n = 0; n < nodes.size(); ++n) source_roots_[n] = unique_parent[n] == none;
    // A portal with a unique incoming chain rooted at a different SOURCE is
    // electrically unreachable by this net, regardless of congestion. Include
    // ALL incoming edges when proving this; cross-die inputs invalidate a purely
    // local root proof. Ambiguous/cyclic chains remain eligible for detailed search.
    for (auto& p : portals_) {
        if (p.edge == none) continue; // Conservative: membership portals need no root proof.
        auto n = p.source;
        std::set<std::uint32_t> seen;
        while (seen.insert(n).second) {
            const auto pred = unique_parent[n];
            if (pred == none) { p.required_root = n; break; }
            if (pred == ambiguous || dies_[pred] != dies_[n]) break;
            n = pred;
        }
    }
}

KernelBatchResult RRBackend::execute(const std::vector<Node>& nodes, const std::vector<Edge>& edges,
    std::vector<Resource>& resources, const std::vector<Task>& tasks,
    const std::vector<std::vector<SearchSeed>>& seeds, bool overuse, const std::vector<WideCost>* costs) {
    if(config_.edge_identity)throw std::invalid_argument("edge-aware backend requires execute_edges");
    return execute_impl(nodes, edges, RRStateView(resources,costs), tasks, seeds, overuse, &resources, nullptr, nullptr);
}

EdgeBatchResult RRBackend::execute_edges(const std::vector<Node>& nodes,const std::vector<Edge>& edges,
    std::vector<Resource>& resources,const std::vector<Task>& tasks,
    const std::vector<std::vector<SearchSeed>>& seeds,bool overuse,const std::vector<WideCost>* costs) {
    if(!config_.edge_identity)throw std::invalid_argument("execute_edges requires edge_identity mode");
    EdgeBatchResult out;
    out.batch=execute_impl(nodes,edges,RRStateView(resources,costs),tasks,seeds,overuse,&resources,nullptr,&out.edge_paths);
    return out;
}

RRProposal RRBackend::propose(const std::vector<Node>& nodes, const std::vector<Edge>& edges,
    const std::vector<Resource>& resources, const Task& task, const std::vector<SearchSeed>& seeds,
    bool overuse, const std::vector<WideCost>* costs) {
    return propose_view(nodes,edges,RRStateView(resources,costs),task,seeds,overuse);
}

RRProposal RRBackend::propose_view(const std::vector<Node>& nodes, const std::vector<Edge>& edges,
    const RRStateView& resources, const Task& task, const std::vector<SearchSeed>& seeds, bool overuse) {
    RRProposal proposal;
    proposal.requires_edge_identity=config_.edge_identity;
    proposal.requires_policy=policy_->active();
    proposal.candidate.task = task;
    const auto start = std::chrono::steady_clock::now();
    const auto saved = metrics_; metrics_ = {};
    try {
        auto batch = execute_impl(nodes, edges, resources, {task}, {seeds}, overuse, nullptr, &proposal, nullptr);
        proposal.candidate = std::move(batch.candidates.at(0));
        proposal.search_metrics = batch.search_metrics; proposal.telemetry = batch.telemetry;
        proposal.work = metrics_; metrics_ = saved;
    } catch (const std::overflow_error&) {
        // A stale occupancy/cost summary can overflow while current authority
        // would not. Keep the partial read journal so ordered validation can
        // retry stale work, but never accept an overflow on a current snapshot.
        proposal.overflowed = true;
        proposal.work = metrics_; metrics_ = saved;
        proposal.work.aborted_reservations = proposal.work.reserved_resources;
        proposal.telemetry.search_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now() - start).count();
    } catch (...) { metrics_ = saved; throw; }
    return proposal;
}

KernelBatchResult RRBackend::execute_impl(const std::vector<Node>& nodes, const std::vector<Edge>& edges,
    const RRStateView& resources, const std::vector<Task>& tasks,
    const std::vector<std::vector<SearchSeed>>& seeds, bool allow_overuse,
    std::vector<Resource>* authoritative, RRProposal* proposal,
    std::vector<std::vector<std::uint32_t>>* edge_paths) {
    if (nodes.size() != dies_.size() || resources.size() != nodes.size() || seeds.size() != tasks.size())
        throw std::invalid_argument("RR executor size mismatch");
    // Native commercial terminal nodes must currently have unambiguous pin SLRs.
    // Refuse multi-SLR terminals until task endpoint access locations are exported.
    for (const auto& t : tasks) {
        if (t.source >= nodes.size() || t.sink >= nodes.size()) throw std::invalid_argument("task endpoint out of range");
        if(!policy_->node_allowed(t.source,t.net_id)||!policy_->node_allowed(t.sink,t.net_id))throw std::invalid_argument("task terminal violates immutable routing policy");
        for (auto n : {t.source, t.sink}) if ((membership_[n] & (membership_[n] - 1U)) != 0)
            throw std::invalid_argument("multi-SLR terminal requires explicit task access die");
    }
    auto member = [&](std::uint32_t n, std::uint16_t d) { return (membership_[n] & (1U << d)) != 0; };
    std::vector<std::size_t> order(tasks.size()); std::iota(order.begin(), order.end(), 0);
    std::sort(order.begin(), order.end(), [&](auto a, auto b) {
        return std::tie(tasks[a].priority, tasks[a].id) < std::tie(tasks[b].priority, tasks[b].id);
    });
    std::set<std::uint32_t> nets, ids;
    for (auto i : order) {
        if (tasks[i].source >= nodes.size() || tasks[i].sink >= nodes.size() || seeds[i].empty() ||
            !nets.insert(tasks[i].net_id).second || !ids.insert(tasks[i].id).second)
            throw std::invalid_argument("invalid batch or more than one task per net");
        for (auto s : seeds[i]) if (s.node >= nodes.size() || !policy_->node_allowed(s.node,tasks[i].net_id)) throw std::invalid_argument("seed out of range or forbidden by routing policy");
    }
    KernelBatchResult out;
    auto& search_metrics = proposal ? proposal->search_metrics : out.search_metrics;
    for (auto index : order) {
        const auto& t = tasks[index];
        const auto start = std::chrono::steady_clock::now();
        std::set<std::uint32_t> tree;
        for (auto s : seeds[index]) tree.insert(s.node);
        KernelCandidate candidate; candidate.task = t;
        std::vector<std::uint32_t> candidate_edges;
        ResourceReader state(resources, proposal ? &proposal->candidate.reads : nullptr);
        auto cost_for = [&](std::uint32_t node){return state.cost(node);};
        std::set<std::uint32_t> banned;
        auto& downstream=downstream_;
        downstream.reset();
        auto prepare_downstream = [&](const std::vector<std::pair<Portal, std::uint64_t>>& choices) {
            // Diagnostic exact local lookahead on THIS resource snapshot. Its
            // full cost is counted, including unsuccessful plans and retries.
            // The source die still uses the geometry estimate. This is not an
            // exact global solver or a claim of a cheap hardware lookahead.
            ++metrics_.downstream_searches;
            downstream.reset();
            SparseNodeTable<std::uint64_t> entry_cost(inf);
            for (const auto& choice : choices) {
                auto& entry = entry_cost.touch(choice.first.destination);
                entry = std::min(entry, choice.second);
            }
            std::uint64_t best_complete = inf;
            using Label = std::pair<std::uint64_t, std::uint32_t>;
            std::priority_queue<Label, std::vector<Label>, std::greater<Label>> queue;
            downstream.touch(t.sink) = 0; queue.push({0, t.sink});
            while (!queue.empty()) {
                const auto [cost, n] = queue.top(); queue.pop();
                if (cost != downstream.get(n)) continue;
                // All portal entry costs are nonnegative. Once the frontier
                // exceeds a complete entry+tail score, no unvisited portal can
                // improve it. Strict '>' retains all equal-score tie candidates.
                if (config_.bound_downstream && cost > best_complete) {
                    ++metrics_.downstream_cutoffs; break;
                }
                if (entry_cost.get(n) != inf) best_complete = std::min(best_complete, add_cost(cost, entry_cost.get(n)));
                ++metrics_.downstream_expanded; ++search_metrics.expanded;
                const auto& resource = state[n];
                if (tree.count(n) || (!allow_overuse && resource.owner != t.net_id && resource.occupancy >= resource.capacity)) continue;
                for (const auto& incoming : incoming_[n]) {
                    if(!policy_->node_allowed(incoming.source,t.net_id))continue;
                    if (edge_die_[incoming.edge] != dies_[t.sink]) continue;
                    ++metrics_.downstream_edge_visits; ++search_metrics.edge_visits;
                    const auto next = add_cost(cost, rr_edge_cost(edges[incoming.edge], resource, t, resource.owner == t.net_id, config_.vpr_style_cost, cost_for(n)));
                    if (next < downstream.get(incoming.source)) {
                        downstream.touch(incoming.source) = next; queue.push({next, incoming.source});
                    }
                }
            }
        };
        bool found = false;
        std::uint64_t best_branch_cost = inf;
        bool selected_corridor = false;
        std::uint64_t selected_reservations = 0;
        bool alternate_entry = false;
        bool has_local_seed = false, has_remote_seed = false;
        for (auto s : seeds[index]) {
            has_local_seed |= member(s.node, dies_[t.sink]);
            has_remote_seed |= (membership_[s.node] & ~(1U << dies_[t.sink])) != 0;
        }
        const bool compare_reentry = config_.downstream_cost && has_local_seed && has_remote_seed;
        for (std::uint32_t attempt = 0; config_.hierarchical && attempt < config_.repair_attempts; ++attempt) {
            ++metrics_.planned;
            // Multi-source shortest die-hop path. It is only a corridor proposal;
            // electrical reachability is checked by the die-local searches below.
            std::vector<std::uint32_t> parent(die_count_, none), die_queue;
            for (auto s : seeds[index]) for (std::uint16_t d = 0; d < die_count_; ++d)
                if (member(s.node, d) && (!alternate_entry || d != dies_[t.sink]) && parent[d] == none) {
                    parent[d] = d; die_queue.push_back(d);
                }
            const auto target_die = dies_[t.sink];
            for (std::size_t qi = 0; qi < die_queue.size() && parent[target_die] == none; ++qi)
                for (const auto& p : portals_) {
                    if(!policy_->node_allowed(p.source,t.net_id)||!policy_->node_allowed(p.destination,t.net_id))continue;
                    const auto to = p.to_die;
                    if (source_roots_[t.source] && p.required_root != none && p.required_root != t.source) continue;
                    if (!banned.count(p.id) && p.from_die == die_queue[qi] && parent[to] == none) {
                        parent[to] = die_queue[qi]; die_queue.push_back(to);
                    }
                }
            if (parent[target_die] == none) break;
            std::vector<std::uint32_t> die_path{target_die};
            while (parent[die_path.back()] != die_path.back()) die_path.push_back(parent[die_path.back()]);
            std::reverse(die_path.begin(), die_path.end());
            std::vector<SearchSeed> frontier;
            for (auto s : seeds[index]) if (member(s.node, die_path.front())) frontier.push_back(s);
            std::vector<Portal> corridor;
            auto estimate_from = frontier;
            bool complete = true;
            for (std::size_t stage = 1; stage < die_path.size(); ++stage) {
                const bool exact_tail = config_.downstream_cost && stage + 1 == die_path.size();
                Portal best{none, none, none, none, none, 0, 0}; std::uint64_t best_score = inf;
                std::vector<std::pair<Portal, std::uint64_t>> choices;
                for (const auto& p : portals_) {
                    if(!policy_->node_allowed(p.source,t.net_id)||!policy_->node_allowed(p.destination,t.net_id))continue;
                    const auto e = p.edge == none ? Edge{p.destination, 0, 0} : edges[p.edge];
                    if (p.from_die != die_path[stage - 1] || p.to_die != die_path[stage] ||
                        banned.count(p.id) || tree.count(e.dst)) continue;
                    if (source_roots_[t.source] && p.required_root != none && p.required_root != t.source) {
                        ++metrics_.structurally_pruned_portals; continue;
                    }
                    if (!allow_overuse && ((!tree.count(p.source) && state[p.source].owner != t.net_id &&
                        state[p.source].occupancy >= state[p.source].capacity) ||
                        (state[e.dst].owner != t.net_id && state[e.dst].occupancy >= state[e.dst].capacity))) continue;
                    auto from = inf;
                    // Rank from the same timing-weighted seeds as detailed
                    // search. A geometrically close tree node is not a free
                    // starting point when its upstream route is slow.
                    for (auto s : estimate_from) from = std::min(from,
                        s.cost_q + config_.geometry_weight * gap(boxes_[s.node], boxes_[p.source]));
                    const bool owns_source = tree.count(p.source) || state[p.source].owner == t.net_id;
                    std::uint64_t source_penalty = 0;
                    if (!config_.vpr_style_cost)
                        source_penalty = rr_edge_cost({p.source, 0, 0}, state[p.source], t, owns_source, false, cost_for(p.source));
                    if (config_.vpr_style_cost) {
                        // Use the cheapest incoming static base cost to estimate
                        // only the source endpoint's extra congestion penalty.
                        std::uint16_t base = 65535;
                        for (const auto& in : incoming_[p.source]) base = std::min(base, edges[in.edge].base_cost_q);
                        if (incoming_[p.source].empty()) base = 0;
                        const Edge estimate{p.source, base, 0};
                        source_penalty = rr_edge_cost(estimate, state[p.source], t, owns_source, true, cost_for(p.source)) -
                                         rr_edge_cost(estimate, state[p.source], t, true, true, cost_for(p.source));
                    }
                    const auto transition = p.edge == none ? 0 : rr_edge_cost(e, state[e.dst], t,
                        tree.count(e.dst) || state[e.dst].owner == t.net_id, config_.vpr_style_cost, cost_for(e.dst));
                    const auto entry = add_cost(from, add_cost(transition, source_penalty));
                    choices.push_back({p, entry});
                }
                if (exact_tail && !choices.empty()) prepare_downstream(choices);
                for (const auto& choice : choices) {
                    const auto& p = choice.first;
                    const auto e = p.edge == none ? Edge{p.destination, 0, 0} : edges[p.edge];
                    if (exact_tail && downstream.get(e.dst) == inf) continue;
                    const auto tail = exact_tail ? downstream.get(e.dst) : config_.geometry_weight * gap(boxes_[e.dst], boxes_[t.sink]);
                    const auto score = add_cost(choice.second, tail);
                    if (std::tie(score, p.source, p.id) < std::tie(best_score, best.source, best.id)) {
                        best = p; best_score = score;
                    }
                }
                if (best.id == none) { complete = false; break; }
                corridor.push_back(best); estimate_from = {{best.destination, 0, 0}};
            }
            if (!complete) break;
            // Reserve the union of endpoint resources. Aliased portals consume
            // one RR resource per net. No occupancy writes occur before success.
            std::vector<ReadEntry> reservation;
            std::set<std::uint32_t> reserved;
            for (const auto& p : corridor) for (auto n : {p.source, p.destination})
                if (reserved.insert(n).second) {
                    reservation.push_back({n, state[n].version});
                    ++metrics_.reserved_resources;
                    if (!tree.count(n) && state[n].owner != t.net_id && state[n].occupancy >= state[n].capacity)
                        ++metrics_.overcapacity_reservations;
                }
            std::set<std::uint32_t> blocked = tree;
            std::vector<std::uint32_t> branch, branch_edges;
            std::uint32_t attachment = none, failed_portal = none;
            for (std::size_t stage = 0; stage <= corridor.size(); ++stage) {
                const auto destination = stage == corridor.size() ? t.sink : corridor[stage].source;
                ++metrics_.local_searches;
                auto segment = search(nodes, edges, state, membership_, edge_die_, die_path[stage], t, frontier, destination,
                                      true, allow_overuse, config_.vpr_style_cost, blocked, search_metrics, *policy_,search_);
                if (!segment.found) {
                    complete = false;
                    if (!corridor.empty()) failed_portal = corridor[std::min(stage, corridor.size() - 1)].id;
                    break;
                }
                if (attachment == none) attachment = segment.attachment;
                branch.insert(branch.end(), segment.path.begin(), segment.path.end());
                branch_edges.insert(branch_edges.end(),segment.edge_path.begin(),segment.edge_path.end());
                for (auto n : segment.path) blocked.insert(n);
                if (stage == corridor.size()) break;
                const auto next = corridor[stage].destination;
                if (corridor[stage].edge == none) {
                    // The boundary is internal to this electrical resource. It
                    // already appears in the branch (or attachment) exactly once.
                    frontier = {{next, segment.hops, 0}};
                    continue;
                }
                if (blocked.count(next) || segment.hops >= t.max_hops) {
                    complete = false; failed_portal = corridor[stage].id; break;
                }
                branch.push_back(next); branch_edges.push_back(corridor[stage].edge); blocked.insert(next);
                frontier = {{next, segment.hops + 1, 0}};
            }
            if (complete) {
                for (auto r : reservation) if (state[r.resource_id].version != r.version)
                    throw std::logic_error("serial reservation changed during local routing");
                // A tree already reaching the target die must not force every
                // later sink to use that entry. Compare the complete incremental
                // branch cost against one newly allocated corridor before commit.
                std::uint64_t score = inf;
                for (auto s : seeds[index]) if (s.node == attachment) score = s.cost_q;
                if(!valid_edge_path(nodes,edges,attachment,branch,branch_edges))throw std::logic_error("candidate edge trace invalid");
                for (std::size_t j=0;j<branch.size();++j) {
                    const auto n=branch[j];
                    const auto step=rr_edge_cost(edges[branch_edges[j]],state[n],t,state[n].owner==t.net_id,config_.vpr_style_cost,cost_for(n));
                    if (score == inf || step == inf) throw std::logic_error("candidate cost lacks RR edge/seed");
                    score = add_cost(score, step);
                }
                if (score < best_branch_cost) {
                    best_branch_cost = score; candidate.attachment = attachment;
                    candidate.path = std::move(branch); found = true; selected_corridor = !corridor.empty();
                    candidate_edges=std::move(branch_edges);
                    selected_reservations = reservation.size();
                } else metrics_.aborted_reservations += reservation.size();
                if (compare_reentry && !alternate_entry) { alternate_entry = true; continue; }
                break;
            }
            metrics_.aborted_reservations += reservation.size();
            if (failed_portal == none) break;
            banned.insert(failed_portal); ++metrics_.repairs;
        }
        if (!found) {
            if (config_.hierarchical) ++metrics_.fallbacks;
            ++metrics_.flat_searches;
            auto segment = search(nodes, edges, state, membership_, edge_die_, 0, t, seeds[index], t.sink,
                                  false, allow_overuse, config_.vpr_style_cost, tree, search_metrics, *policy_,search_);
            found = segment.found; candidate.attachment = segment.attachment;
            candidate.path = std::move(segment.path);
            candidate_edges=std::move(segment.edge_path);
        }
        candidate.search_status = found ? 1 : 2;
        out.telemetry.search_ns += std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now() - start).count();
        if (!found) { ++search_metrics.failed; candidate.commit_status = 2; }
        else {
            if(!valid_edge_path(nodes,edges,candidate.attachment,candidate.path,candidate_edges))throw std::logic_error("selected edge trace invalid");
            if(!policy_->path_allowed(t,candidate.attachment,candidate.path,candidate_edges))throw std::logic_error("selected path violates immutable routing policy");
            const auto commit_start = std::chrono::steady_clock::now();
            std::set<std::uint32_t> unique;
            for (auto n : candidate.path) {
                if (!unique.insert(n).second || tree.count(n)) throw std::logic_error("branch repeats tree resource");
                if (state[n].version == none || state[n].occupancy == 65535)
                    throw std::overflow_error("RR version/occupancy overflow: no commit performed");
                if (!allow_overuse && state[n].owner != t.net_id && state[n].occupancy >= state[n].capacity)
                    throw std::logic_error("serial capacity changed before commit");
                if (!proposal) candidate.reads.push_back({n, state[n].version});
            }
            if (proposal) {
                proposal->corridor = selected_corridor;
                proposal->selected_reservations = selected_reservations;
                auto previous = candidate.attachment;
                for (auto n : candidate.path) { proposal->owner_changes += dies_[previous] != dies_[n]; previous = n; }
                candidate.commit_status = 0;
            } else {
            auto previous = candidate.attachment;
            for (auto n : candidate.path) {
                metrics_.committed_crossings += dies_[previous] != dies_[n]; previous = n;
                auto& resource = (*authoritative)[n];
                if (resource.owner != t.net_id) {
                    resource.owner = resource.occupancy == 0 ? t.net_id : none;
                    ++resource.occupancy; ++resource.version;
                }
            }
            candidate.commit_status = 4; ++out.commit_metrics.commits;
            if (selected_corridor) ++metrics_.committed_corridors;
            }
            out.telemetry.commit_ns += std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::steady_clock::now() - commit_start).count();
        }
        if (proposal) {candidate.reads = std::move(proposal->candidate.reads);proposal->edge_path=candidate_edges;}
        if(edge_paths)edge_paths->push_back(std::move(candidate_edges));
        out.candidates.push_back(std::move(candidate));
    }
    if (proposal) out.search_metrics = proposal->search_metrics;
    return out;
}
} // namespace dieroute
