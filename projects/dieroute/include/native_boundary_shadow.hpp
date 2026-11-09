#pragma once
#include "native_route_state.hpp"
#include <memory>

namespace dieroute {
// Sparse CPU reference for native multi-SLR electrical nodes. The lowest member
// SLR owns each summary. The full membership mask remains the topology identity;
// assigning a summary owner does not split or duplicate an electrical resource.
// Local/nonboundary reads still use the serial authority. No concurrent mutation
// is allowed during a search or between validation and accept().
class NativeBoundaryShadows {
public:
    struct Summary {
        std::uint64_t occupancy=0,history=0,version=0;
        bool operator==(const Summary& b)const {
            return std::tie(occupancy,history,version)==std::tie(b.occupancy,b.history,b.version);
        }
    };
    struct Metrics {std::uint64_t publications=0,changed_summaries=0,logical_deliveries=0;};
private:
    using Snapshot=std::map<std::uint32_t,Summary>;
    std::shared_ptr<const Snapshot> snapshot_;
    std::uint64_t epoch_=0;
    std::uint32_t dies_;
    Metrics metrics_;
    static Summary summarize(const NativeRouteState& state,std::uint32_t node) {
        const auto it=state.find_use(node);
        return !it?Summary{}:Summary{it->nets.size(),it->history,it->version};
    }
    static Summary lookup(const Snapshot& snapshot,std::uint32_t node) {
        const auto it=snapshot.find(node);return it==snapshot.end()?Summary{}:it->second;
    }
    bool boundary(std::uint32_t mask)const {
        if(!mask || mask>=(1U<<dies_))throw std::invalid_argument("invalid native SLR membership");
        return (mask&(mask-1))!=0;
    }
public:
    explicit NativeBoundaryShadows(std::uint32_t dies):dies_(dies) {
        if(!dies || dies>8)throw std::invalid_argument("invalid native shadow die count");
    }
    NativeBoundaryShadows(const NativeBoundaryShadows&)=delete;
    NativeBoundaryShadows& operator=(const NativeBoundaryShadows&)=delete;
    const Metrics& metrics()const{return metrics_;}
    std::size_t records()const{return snapshot_?snapshot_->size():0;}
    template<class Emit> void summaries(Emit emit)const {
        if(!snapshot_)throw std::logic_error("unpublished native boundary summaries");
        for(const auto& [n,s]:*snapshot_)emit(n,s);
    }
    // Whole-checkpoint replacement must invalidate every earlier view, including
    // checkpoints whose resource versions happen to equal the old versions.
    void invalidate() {
        if(epoch_==UINT64_MAX)throw std::overflow_error("native shadow epoch exhausted");
        ++epoch_;snapshot_.reset();
    }
    template<class Membership> void publish(const NativeRouteState& state,Membership membership) {
        auto next=std::make_shared<Snapshot>();std::uint64_t changed=0;
        state.visit_uses([&](auto n,const auto& u){if(!boundary(membership(n)))return;
            Summary value{u.nets.size(),u.history,u.version};
            const auto old=snapshot_?lookup(*snapshot_,n):Summary{};
            if(value.version<old.version || (value.version==old.version && !(value==old)))
                throw std::logic_error("native boundary update lacks monotonic version");
            changed+=!(value==old);next->emplace(n,value);
        });
        // Ripup keeps tombstones. Silently dropping one would reintroduce ABA.
        if(snapshot_)for(const auto& [n,v]:*snapshot_){(void)v;
            if(!next->count(n))throw std::logic_error("native boundary tombstone removed without epoch invalidation");}
        snapshot_=std::move(next);++metrics_.publications;metrics_.changed_summaries+=changed;
        metrics_.logical_deliveries+=changed*(dies_-1);
    }
    class View {
        const NativeBoundaryShadows& owner_;
        std::shared_ptr<const Snapshot> snapshot_;
        std::uint64_t epoch_,present_;
        std::uint32_t observer_,net_;
        Snapshot reads_;
    public:
        View(const NativeBoundaryShadows& owner,std::uint32_t observer,std::uint32_t net,std::uint64_t present)
            :owner_(owner),snapshot_(owner.snapshot_),epoch_(owner.epoch_),present_(present),observer_(observer),net_(net) {
            if(!snapshot_ || observer>=owner.dies_ || net==UINT32_MAX)throw std::invalid_argument("invalid native shadow view");
        }
        std::size_t reads()const{return reads_.size();}
        template<class Emit> void observations(const NativeRouteState& state,Emit emit)const {
            for(const auto& [n,s]:reads_)emit(n,s,summarize(state,n));
        }
        std::uint64_t read_hash()const {
            std::uint64_t h=1469598103934665603ULL;
            auto word=[&](std::uint64_t x){for(unsigned i=0;i<8;++i){h^=(x>>(8*i))&255;h*=1099511628211ULL;}};
            word(epoch_);word(observer_);word(net_);word(present_);
            for(const auto& [n,s]:reads_){word(n);word(s.occupancy);word(s.history);word(s.version);}return h;
        }
        std::uint64_t cost(const NativeRouteState& state,std::uint32_t node,std::uint32_t membership) {
            const bool multi=owner_.boundary(membership);
            const auto owner_bit=membership&(~membership+1U);
            // Existing shared-tree nodes are authoritative seeds and are never
            // charged by SparseSearch. Keep same-net queries correct as well.
            if(!multi || owner_bit==(1U<<observer_) || state.tree(net_).nodes.count(node))
                return state.cost(node,net_,present_);
            const auto s=lookup(*snapshot_,node);reads_.emplace(node,s);
            // A non-tree node cannot be owned by this net in a valid checkpoint.
            // Summaries therefore need no writable or replicated net owner set.
            if(s.history>=UINT64_MAX-1 || (s.occupancy && present_>(UINT64_MAX-2-s.history)/s.occupancy))
                throw std::overflow_error("native shadow cost overflow");
            return 1+s.history+present_*s.occupancy;
        }
        bool valid(const NativeRouteState& state)const {
            if(epoch_!=owner_.epoch_)return false;
            for(const auto& [n,s]:reads_)if(!(s==summarize(state,n)))return false;
            return true;
        }
    };
    View view(std::uint32_t observer,std::uint32_t net,std::uint64_t present)const{return View(*this,observer,net,present);}
};
} // namespace dieroute
