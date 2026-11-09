#pragma once
#include "sparse_label_worker.hpp"
#include <algorithm>
#include <array>
#include <cstdint>
#include <limits>
#include <optional>
#include <stdexcept>
#include <tuple>
#include <type_traits>
#include <vector>

namespace dieroute {
struct SparseSeed {std::uint32_t node,hops;std::uint64_t cost;};
enum class SparseSearchStatus {found,exhausted,budget_exhausted,hop_limited,cost_limited};
struct SparseSearchResult {
    SparseSearchStatus status=SparseSearchStatus::exhausted;
    std::uint32_t attachment=UINT32_MAX,hops=0;
    std::uint64_t cost=0,expanded=0,edge_visits=0;
    std::vector<std::uint32_t> path,edges;
};
struct SparseSearchLimits {
    std::size_t labels=std::numeric_limits<std::size_t>::max();
    std::uint64_t expanded=UINT64_MAX;
    std::uint64_t max_cost=UINT64_MAX;
};
// Same single-label cost/hops/node/parent tie order as RRBackend. It is not a
// Pareto solver for resource-constrained shortest paths. A hop cutoff is exposed
// separately from a proven exhausted search. Caller owns physical costs/policy.
class SparseSearch {
    using Label=SparseLabel;
    using Entry=SparseQueueEntry;
public:
    using WorkerMetrics=SparseWorkerMetrics;
private:
    std::array<SparseLabelWorker,8> workers_;
    std::uint32_t count_=1;
    std::uint64_t epoch_=0,request_id_=0;
    std::vector<LabelPacket> packets_;
    std::uint64_t next_id(){if(request_id_==UINT64_MAX)throw std::overflow_error("label request id exhausted");return ++request_id_;}
    template<class Partition> LabelPacket exchange(const LabelPacket& request,Partition partition,bool credit){
        // Exercise the exact little-endian boundary in both directions. This
        // serial transport has no host-pointer shortcut to receiver labels.
        auto bytes=request.encode();auto wire=LabelPacket::decode(bytes.data());packets_.push_back(wire);
        auto reply=workers_[wire.to()].receive(wire,partition,credit);bytes=reply.encode();reply=LabelPacket::decode(bytes.data());
        packets_.push_back(reply);LabelPacket::match(request,reply);return reply;
    }
    static Label unpack(const LabelPacket& p){
        if(p.status()!=LabelStatus::ok)throw std::logic_error("label probe rejected");
        Label l;l.cost=p.cost();l.hops=p.hops();l.parent=p.parent();l.edge=p.edge();l.version=p.version();
        l.closed=p.flags()&LabelPacket::closed;l.root=p.flags()&LabelPacket::root;return l;
    }
    // Deterministic reference arbiter: one global minimum across independent
    // worker queues. This preserves the single-queue tie order; no concurrency
    // or speedup is implied. Labels live only in their assigned worker table.
    std::uint32_t next_worker()const{
        auto best=count_;
        for(std::uint32_t d=0;d<count_;++d){
            if(!workers_[d].empty()&&(best==count_||workers_[d].head()<workers_[best].head()))best=d;
        }
        return best;
    }
public:
    std::size_t touched()const{std::size_t n=0;for(const auto& w:workers_)n+=w.size();return n;}
    std::size_t retained_bytes()const{std::size_t n=0;for(const auto& w:workers_)n+=w.retained_bytes();return n+packets_.capacity()*sizeof(LabelPacket);}
    std::uint32_t worker_count()const{return count_;}
    WorkerMetrics worker_metrics(std::uint32_t die)const{
        if(die>=count_)throw std::invalid_argument("sparse worker metrics range");
        return workers_[die].metrics();
    }
    const auto& packets()const{return packets_;}
    // expand(node, offer) filters static edge/die policy before offer. offer
    // accepts a lazy optional-cost callback, invoked only for open nonroots;
    // this preserves capacity/version read journals and overflow semantics.
    template<class Expand> SparseSearchResult run(std::uint64_t node_count,
        const std::vector<SparseSeed>& seeds,std::uint32_t sink,std::uint32_t max_hops,
        Expand expand,SparseSearchLimits limits={},std::uint64_t* expanded_counter=nullptr,
        std::uint64_t* edge_counter=nullptr) {
        return run_guided(node_count,seeds,sink,max_hops,expand,[](std::uint32_t){return std::uint64_t(0);},limits,expanded_counter,edge_counter);
    }
    // Potential must be stable, nonnegative, consistent for every permitted
    // edge, and zero at the sink. UINT64_MAX means proven unreachable in a
    // relaxation containing all permitted edges. Caller proves that contract;
    // arbitrary geometric/weighted estimates are NOT admissible by default.
    template<class Expand,class Potential> SparseSearchResult run_guided(std::uint64_t node_count,
        const std::vector<SparseSeed>& seeds,std::uint32_t sink,std::uint32_t max_hops,
        Expand expand,Potential potential,SparseSearchLimits limits={},std::uint64_t* expanded_counter=nullptr,
        std::uint64_t* edge_counter=nullptr) {
        return run_guided_partitioned(node_count,seeds,sink,max_hops,1,[](std::uint32_t){return 0U;},expand,potential,limits,expanded_counter,edge_counter);
    }
    // partition(node) is immutable during the call and returns one worker. The
    // caller filters physical arcs before offer; transfer creates no graph edge,
    // extra cost, hop, resource copy or second search label for the same node.
    template<class Partition,class Expand,class Potential> SparseSearchResult run_guided_partitioned(std::uint64_t node_count,
        const std::vector<SparseSeed>& seeds,std::uint32_t sink,std::uint32_t max_hops,
        std::uint32_t workers,Partition partition,Expand expand,Potential potential,SparseSearchLimits limits={},
        std::uint64_t* expanded_counter=nullptr,std::uint64_t* edge_counter=nullptr){
        if(!workers||workers>8)throw std::invalid_argument("sparse worker count");
        auto owner=[&](std::uint32_t n){auto d=partition(n);if(d>=workers)throw std::invalid_argument("sparse worker assignment");return d;};
        if(sink>=node_count || node_count>UINT32_MAX)throw std::invalid_argument("sparse search node range");
        if(epoch_==UINT64_MAX)throw std::overflow_error("label search epoch exhausted");
        ++epoch_;request_id_=0;packets_.clear();count_=workers;
        for(std::uint32_t d=0;d<8;++d)workers_[d].reset(d,epoch_,node_count);
        if(potential(sink)!=0)throw std::invalid_argument("sparse potential must be zero at sink");
        SparseSearchResult out;bool cutoff=false,hop_cutoff=false,cost_cutoff=false;
        for(const auto& s:seeds) {
            if(s.node>=node_count)throw std::invalid_argument("sparse seed range");
            if(s.cost==UINT64_MAX)throw std::invalid_argument("nonfinite sparse seed cost");
            if(s.hops>max_hops){hop_cutoff=true;continue;}
            const auto h=potential(s.node);if(h==UINT64_MAX)continue;
            if(h>=UINT64_MAX-s.cost)throw std::overflow_error("sparse priority exceeds finite u64");
            if(s.cost+h>limits.max_cost){cost_cutoff=true;continue;}
            const auto target=owner(s.node);
            if(!workers_[target].seed(s.node,s.cost,s.cost+h,s.hops,touched()<limits.labels)){out.status=SparseSearchStatus::budget_exhausted;return out;}
        }
        while(true) {
            const auto active=next_worker();if(active==count_)break;
            const auto [priority,cost,depth,current,predecessor]=workers_[active].pop();(void)predecessor;(void)priority;
            if(owner(current)!=active)throw std::logic_error("foreign node in worker queue");
            const auto value=workers_[active].local(current);
            if(value.closed || cost!=value.cost || depth!=value.hops)continue;
            if(out.expanded>=limits.expanded){out.status=SparseSearchStatus::budget_exhausted;return out;}
            workers_[active].close(current);++out.expanded;
            if(expanded_counter)++*expanded_counter;
            if(current==sink) {
                out.status=SparseSearchStatus::found;out.cost=cost;out.hops=depth;auto n=current;
                for(std::size_t count=0;;++count) {
                    if(count>touched())throw std::logic_error("sparse parent cycle");
                    const auto label=count_==1?workers_[0].local(n):unpack(exchange(LabelPacket::message(epoch_,next_id(),n,LabelOp::trace,LabelPacket::controller,owner(n)),owner,false));
                    if(label.parent==UINT32_MAX)break;
                    out.path.push_back(n);out.edges.push_back(label.edge);n=label.parent;
                }
                out.attachment=n;std::reverse(out.path.begin(),out.path.end());std::reverse(out.edges.begin(),out.edges.end());return out;
            }
            if(depth>=max_hops){hop_cutoff=true;continue;}
            expand(current,[&](std::uint32_t dst,std::uint32_t edge,auto evaluate) {
                if(cutoff)return;
                if(dst>=node_count)throw std::invalid_argument("sparse destination range");
                ++out.edge_visits;workers_[active].visit();if(edge_counter)++*edge_counter;
                const auto target=owner(dst);const bool remote=target!=active;
                const auto id=remote?next_id():0;
                const auto old=remote?unpack(exchange(LabelPacket::message(epoch_,id,dst,LabelOp::probe,active,target),owner,false)):workers_[active].local(dst);
                if(old.closed || old.root)return;
                const std::optional<std::uint64_t> delta=evaluate();if(!delta)return;
                if(*delta>=UINT64_MAX-cost)throw std::overflow_error("RR accumulated cost exceeds finite u64");
                const auto next=cost+*delta;const auto hops=depth+1;
                if(std::tie(next,hops,current,edge)<std::tie(old.cost,old.hops,old.parent,old.edge)) {
                    const auto h=potential(dst);if(h==UINT64_MAX)return;
                    if(h>=UINT64_MAX-next)throw std::overflow_error("sparse priority exceeds finite u64");
                    if(next+h>limits.max_cost){cost_cutoff=true;return;}
                    auto request=LabelPacket::message(epoch_,remote?id:next_id(),dst,LabelOp::relax,active,target);
                    request.value(next,next+h,hops,current,edge,0,old.version);
                    const auto reply=remote?exchange(request,owner,touched()<limits.labels):workers_[active].receive(request,owner,touched()<limits.labels);
                    if(reply.status()==LabelStatus::budget){cutoff=true;return;}
                    if(reply.status()==LabelStatus::overflow)throw std::overflow_error("search label version exhausted");
                    if(reply.status()!=LabelStatus::accepted)throw std::logic_error("serialized label relaxation invalidated");
                }
            });
            if(cutoff){out.status=SparseSearchStatus::budget_exhausted;return out;}
        }
        out.status=hop_cutoff?SparseSearchStatus::hop_limited:cost_cutoff?SparseSearchStatus::cost_limited:SparseSearchStatus::exhausted;return out;
    }
};
} // namespace dieroute
