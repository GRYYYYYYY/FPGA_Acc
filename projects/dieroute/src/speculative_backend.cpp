#include "speculative_backend.hpp"
#include <algorithm>
#include <chrono>
#include <future>
#include <limits>
#include <numeric>
#include <set>
#include <stdexcept>
#include <tuple>

namespace dieroute {
using namespace persistroute;
namespace {
constexpr auto none = std::numeric_limits<std::uint32_t>::max();
std::uint64_t hash_word(std::uint64_t hash,std::uint64_t value) {
    for(unsigned b=0;b<8;++b){hash^=(value>>(8*b))&255;hash*=1099511628211ULL;}return hash;
}
std::uint64_t read_hash(const RRProposal& p) {
    std::uint64_t hash=1469598103934665603ULL;
    for(auto r:p.candidate.reads){hash=hash_word(hash,r.resource_id);hash=hash_word(hash,r.version);}return hash;
}
bool same(const BoundaryShadow& a, const BoundaryShadow& b) {
    return std::tie(a.capacity,a.occupancy,a.version,a.present_q,a.history_q,a.valid) ==
           std::tie(b.capacity,b.occupancy,b.version,b.present_q,b.history_q,b.valid);
}
WideCost cost(const Resource& r, const std::vector<WideCost>* costs, std::size_t n) {
    return costs ? costs->at(n) : WideCost{r.present_cost_q,r.history_cost_q};
}
std::vector<bool> boundaries(const std::vector<Node>& nodes, const std::vector<Edge>& edges,
                            const std::vector<std::uint16_t>& owners, const std::vector<std::uint16_t>& members) {
    if(owners.size()!=nodes.size() || (!members.empty() && members.size()!=nodes.size()))
        throw std::invalid_argument("boundary topology size mismatch");
    std::vector<bool> out(nodes.size());
    for(std::size_t n=0;n<nodes.size();++n) {
        if(!members.empty()) out[n]=(members[n]&(members[n]-1U))!=0;
        if(std::uint64_t(nodes[n].edge_begin)+nodes[n].edge_count>edges.size())throw std::invalid_argument("invalid CSR");
        for(std::uint32_t i=0;i<nodes[n].edge_count;++i) {
            const auto dst=edges[nodes[n].edge_begin+i].dst;
            if(dst>=nodes.size())throw std::invalid_argument("invalid edge destination");
            if(members.empty() && owners[n]!=owners[dst])out[n]=out[dst]=true;
        }
    }
    return out;
}
void add_work(RRBackendMetrics& a,const RRBackendMetrics& b) {
#define ADD(field) a.field+=b.field
    ADD(planned);ADD(local_searches);ADD(flat_searches);ADD(reserved_resources);ADD(aborted_reservations);
    ADD(committed_corridors);ADD(repairs);ADD(fallbacks);ADD(committed_crossings);ADD(overcapacity_reservations);
    ADD(structurally_pruned_portals);ADD(downstream_searches);ADD(downstream_expanded);
    ADD(downstream_edge_visits);ADD(downstream_cutoffs);
#undef ADD
}
}
BoundaryShadows::BoundaryShadows(std::vector<std::uint16_t> owners,std::vector<bool> boundary)
    : owners_(std::move(owners)),boundary_(std::move(boundary)) {
    if(owners_.empty() || boundary_.size()!=owners_.size())throw std::invalid_argument("invalid shadow topology");
    const auto dies=1+*std::max_element(owners_.begin(),owners_.end());
    if(dies>8)throw std::invalid_argument("unsupported shadow die count");
    if(owners_.size()>none)throw std::invalid_argument("shadow node ID range");
    for(std::uint32_t n=0;n<owners_.size();++n)if(boundary_[n]) {
        boundary_index_.emplace(n,boundary_nodes_.size());boundary_nodes_.push_back(n);
    }
    latest_.resize(boundary_nodes_.size());
    replicas_.assign(dies,std::vector<BoundaryShadow>(boundary_nodes_.size()));
}
void BoundaryShadows::stage(const std::vector<Resource>& resources,const std::vector<WideCost>* costs) {
    if(resources.size()!=owners_.size() || (costs && costs->size()!=resources.size()))throw std::invalid_argument("shadow state size mismatch");
    auto next=latest_;
    for(std::size_t index=0;index<boundary_nodes_.size();++index) {
        auto n=boundary_nodes_[index];
        const auto& r=resources[n];const auto c=cost(r,costs,n);
        BoundaryShadow value{r.capacity,r.occupancy,r.version,c.present_q,c.history_q,true};
        if(!value.capacity || (latest_[index].valid && (value.version<latest_[index].version ||
           (value.version==latest_[index].version && !same(value,latest_[index])))))
            throw std::logic_error("boundary authority changed without a monotonic version");
        next[index]=value;
    }
    latest_=std::move(next);
}
bool BoundaryShadows::receive(std::uint16_t target,const ShadowMessage& message) {
    const auto n=message.resource;
    if(n>=owners_.size() || target>=replicas_.size() || !boundary_[n] || target==owners_[n] ||
       message.owner_die!=owners_[n] || !message.value.valid || !message.value.capacity)
        throw std::invalid_argument("invalid boundary shadow message");
    auto& current=replicas_[target][boundary_index_.at(n)];
    if(current.valid && message.value.version<current.version){++metrics_.stale_dropped;return false;}
    if(current.valid && message.value.version==current.version) {
        if(!same(current,message.value))throw std::logic_error("conflicting shadow values at the same version");
        return false;
    }
    current=message.value;++metrics_.published;metrics_.payload_bytes+=32;return true;
}
void BoundaryShadows::publish() {
    for(std::size_t i=0;i<boundary_nodes_.size();++i)if(latest_[i].valid) {
        auto n=boundary_nodes_[i];
        for(std::uint16_t die=0;die<replicas_.size();++die)if(die!=owners_[n])receive(die,{n,owners_[n],latest_[i]});
    }
}
bool BoundaryShadows::remote_boundary(std::uint16_t die,std::uint32_t n) const {
    return boundary_.at(n) && owners_[n]!=die;
}
RRStateView BoundaryShadows::view(std::uint16_t die,const std::vector<Resource>& resources,
                                 const std::vector<WideCost>* costs) const {
    if(die>=replicas_.size() || resources.size()!=owners_.size() || (costs && costs->size()!=resources.size()))
        throw std::invalid_argument("invalid shadow view");
    auto overlay=std::make_shared<RRStateOverlay>();
    for(std::size_t i=0;i<boundary_nodes_.size();++i) {
        auto n=boundary_nodes_[i];
        if(remote_boundary(die,n)) {
            const auto& s=replicas_[die][i];
            if(!s.valid)throw std::logic_error("uninitialized boundary shadow");
            auto r=resources[n];r.capacity=s.capacity;r.occupancy=s.occupancy;r.version=s.version;
            overlay->emplace(n,RRStateOverride{r,{s.present_q,s.history_q}});
            // Owner is an authoritative read from this window's snapshot. It is
            // NEVER stored in the shadow. A stale summary still carries its old
            // version, forcing validation/replay before this mixed view can commit.
        }
    }
    return RRStateView(resources,costs,std::move(overlay));
}
static ProposalCommit commit_impl(std::vector<Resource>& resources,const RRProposal& proposal,bool overuse,
    const std::vector<Node>* nodes,const std::vector<Edge>* edges,const RoutingPolicy* policy) {
    const auto& candidate=proposal.candidate;
    std::set<std::uint32_t> reads,writes;
    bool stale=false;
    for(const auto& read:candidate.reads) {
        if(read.resource_id>=resources.size() || !reads.insert(read.resource_id).second)return ProposalCommit::invalid;
        stale|=resources[read.resource_id].version!=read.version;
    }
    if(stale)return ProposalCommit::stale;
    if(proposal.overflowed)return ProposalCommit::overflow;
    if(candidate.search_status==2)return ProposalCommit::unreachable;
    if(candidate.search_status!=1 || candidate.attachment>=resources.size())return ProposalCommit::invalid;
    if((proposal.requires_edge_identity && !nodes) ||
       (nodes && !valid_edge_path(*nodes,*edges,candidate.attachment,candidate.path,proposal.edge_path)))return ProposalCommit::invalid;
    if(proposal.requires_policy && (!policy || !policy->active()))return ProposalCommit::invalid;
    if(policy){policy->validate(nodes->size(),edges->size());
        if(candidate.task.source>=nodes->size() || candidate.task.sink>=nodes->size() ||
           !policy->path_allowed(candidate.task,candidate.attachment,candidate.path,proposal.edge_path))return ProposalCommit::invalid;}
    for(auto n:candidate.path) {
        if(n>=resources.size() || !writes.insert(n).second || !reads.count(n))return ProposalCommit::invalid;
        const auto& r=resources[n];
        if(r.version==none || r.occupancy==65535)return ProposalCommit::overflow;
        if(!overuse && r.owner!=candidate.task.net_id && r.occupancy>=r.capacity)return ProposalCommit::capacity;
    }
    for(auto n:candidate.path) {
        auto& r=resources[n];
        if(r.owner!=candidate.task.net_id) { r.owner=r.occupancy?none:candidate.task.net_id;++r.occupancy;++r.version; }
    }
    return ProposalCommit::committed;
}
ProposalCommit commit_proposal(std::vector<Resource>& resources,const RRProposal& proposal,bool overuse) {
    return commit_impl(resources,proposal,overuse,nullptr,nullptr,nullptr);
}
ProposalCommit commit_proposal(std::vector<Resource>& resources,const RRProposal& proposal,bool overuse,
    const std::vector<Node>& nodes,const std::vector<Edge>& edges,const RoutingPolicy& policy) {
    return commit_impl(resources,proposal,overuse,&nodes,&edges,&policy);
}
SpeculativeBackend::SpeculativeBackend(const std::vector<Node>& nodes,const std::vector<Edge>& edges,
    std::vector<std::uint16_t> owners,std::vector<RRBox> boxes,RRBackendConfig config,
    std::vector<std::uint16_t> membership,std::vector<std::uint16_t> edge_die,std::uint32_t workers,std::uint32_t sync,RoutingPolicyPtr policy)
    : edge_identity_(config.edge_identity),policy_(policy?std::move(policy):std::make_shared<RoutingPolicy>()),owners_(std::move(owners)),shadows_(owners_,boundaries(nodes,edges,owners_,membership)),sync_windows_(sync) {
    if(!workers || workers>32 || !sync)throw std::invalid_argument("invalid speculative workers/shadow interval");
    for(std::uint32_t i=0;i<workers;++i)workers_.push_back(std::make_unique<RRBackend>(nodes,edges,owners_,boxes,config,membership,edge_die,policy_));
}
KernelBatchResult SpeculativeBackend::execute(const std::vector<Node>& nodes,const std::vector<Edge>& edges,
    std::vector<Resource>& resources,const std::vector<Task>& tasks,const std::vector<std::vector<SearchSeed>>& seeds,
    bool overuse,const std::vector<WideCost>* costs) {
    if(edge_identity_)throw std::invalid_argument("edge-aware speculative backend requires execute_edges");
    return execute_impl(nodes,edges,resources,tasks,seeds,overuse,costs).batch;
}
EdgeBatchResult SpeculativeBackend::execute_edges(const std::vector<Node>& nodes,const std::vector<Edge>& edges,
    std::vector<Resource>& resources,const std::vector<Task>& tasks,const std::vector<std::vector<SearchSeed>>& seeds,
    bool overuse,const std::vector<WideCost>* costs) {
    if(!edge_identity_)throw std::invalid_argument("execute_edges requires edge_identity mode");
    return execute_impl(nodes,edges,resources,tasks,seeds,overuse,costs);
}
EdgeBatchResult SpeculativeBackend::execute_impl(const std::vector<Node>& nodes,const std::vector<Edge>& edges,
    std::vector<Resource>& resources,const std::vector<Task>& tasks,const std::vector<std::vector<SearchSeed>>& seeds,
    bool overuse,const std::vector<WideCost>* costs) {
    if(tasks.size()!=seeds.size() || nodes.size()!=owners_.size())throw std::invalid_argument("invalid speculative batch");
    std::set<std::uint32_t> ids,nets;
    for(std::size_t i=0;i<tasks.size();++i) {
        const auto& t=tasks[i];
        if(t.source>=nodes.size() || t.sink>=nodes.size() || seeds[i].empty() ||
           !ids.insert(t.id).second || !nets.insert(t.net_id).second || t.epoch!=tasks.front().epoch)
            throw std::invalid_argument("invalid speculative task/epoch/net");
    }
    std::vector<std::size_t> order(tasks.size());std::iota(order.begin(),order.end(),0);
    std::sort(order.begin(),order.end(),[&](auto a,auto b){return std::tie(tasks[a].epoch,tasks[a].priority,tasks[a].id)<
        std::tie(tasks[b].epoch,tasks[b].priority,tasks[b].id);});
    EdgeBatchResult extended;auto& result=extended.batch;
    auto account=[&](const RRProposal& p,std::uint16_t die,bool used_shadows) {
        add_work(work_,p.work);++metrics_.proposals;metrics_.read_entries+=p.candidate.reads.size();
        if(used_shadows)for(const auto& r:p.candidate.reads)metrics_.remote_shadow_reads+=shadows_.remote_boundary(die,r.resource_id);
        result.search_metrics.expanded+=p.search_metrics.expanded;result.search_metrics.edge_visits+=p.search_metrics.edge_visits;
        result.telemetry.search_ns+=p.telemetry.search_ns;++result.telemetry.search_launches;
    };
    for(std::size_t begin=0;begin<order.size();begin+=workers_.size()) {
        shadows_.stage(resources,costs);
        if(metrics_.windows%sync_windows_==0)shadows_.publish();
        const auto count=std::min(workers_.size(),order.size()-begin);
        ++metrics_.windows;metrics_.maximum_window_tasks=std::max(metrics_.maximum_window_tasks,static_cast<std::uint32_t>(count));
        std::vector<std::future<RRProposal>> futures;
        for(std::size_t slot=0;slot<count;++slot) {
            const auto index=order[begin+slot];
            auto view=shadows_.view(owners_[tasks[index].source],resources,costs);
            futures.push_back(std::async(std::launch::async,[&,slot,index,view=std::move(view)]() {
                return workers_[slot]->propose_view(nodes,edges,view,tasks[index],seeds[index],overuse);
            }));
        }
        // All workers finish reading immutable snapshots before authority writes.
        // CPU scheduling cannot change this fixed commit order.
        std::vector<RRProposal> proposals;
        for(auto& future:futures)proposals.push_back(future.get());
        for(std::size_t slot=0;slot<count;++slot) {
            const auto index=order[begin+slot];auto proposal=std::move(proposals[slot]);
            account(proposal,owners_[tasks[index].source],true);
            TransactionTrace trace{};trace.window=metrics_.windows-1;trace.task=tasks[index].id;
            trace.epoch=tasks[index].epoch;trace.priority=tasks[index].priority;
            trace.initial_read_hash=read_hash(proposal);trace.initial_reads=proposal.candidate.reads.size();
            auto commit=[&]() {
                const auto start=std::chrono::steady_clock::now();
                const auto status=commit_proposal(resources,proposal,overuse,nodes,edges,*policy_);
                ++result.telemetry.commit_launches;
                result.telemetry.commit_ns+=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-start).count();
                return status;
            };
            auto status=commit();
            trace.initial_status=status;
            if(status==ProposalCommit::stale) {
                ++metrics_.conflicts;++metrics_.replays;++result.commit_metrics.conflicts;
                work_.aborted_reservations+=proposal.selected_reservations;
                proposal=workers_[slot]->propose(nodes,edges,resources,tasks[index],seeds[index],overuse,costs);
                account(proposal,owners_[tasks[index].source],false);
                trace.replay_read_hash=read_hash(proposal);
                trace.replayed=true;
                status=commit();
                if(status==ProposalCommit::stale)throw std::logic_error("fresh ordered replay became stale");
            }
            if(status==ProposalCommit::invalid || status==ProposalCommit::overflow)
                throw std::runtime_error("transaction rejected invalid/overflowing proposal before mutation");
            if(status==ProposalCommit::committed) {
                proposal.candidate.commit_status=4;++result.commit_metrics.commits;
                work_.committed_corridors+=proposal.corridor;work_.committed_crossings+=proposal.owner_changes;
            } else {proposal.candidate.commit_status=2;++result.search_metrics.failed;}
            trace.final_status=status;trace.final_reads=proposal.candidate.reads.size();
            trace.path_hash=hash_word(1469598103934665603ULL,proposal.candidate.attachment);
            for(auto n:proposal.candidate.path)trace.path_hash=hash_word(trace.path_hash,n);
            if(edge_identity_)for(auto e:proposal.edge_path)trace.path_hash=hash_word(trace.path_hash,e);
            trace_.push_back(trace);
            result.candidates.push_back(std::move(proposal.candidate));
            extended.edge_paths.push_back(std::move(proposal.edge_path));
        }
    }
    return extended;
}
} // namespace dieroute
