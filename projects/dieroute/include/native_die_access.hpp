#pragma once
#include "native_route_state.hpp"
#include <array>
namespace dieroute {
// Demand-filled immutable boundary summaries for one serial candidate phase.
// Workers read only their own authority. A remote boundary read requests a
// summary from its unique owner; no net-owner list crosses that interface.
// The controller generation guards local reads and checkpoint replacement too.
// A concurrent implementation needs explicit owner synchronization; this class
// must not be read while another thread mutates NativeRouteState.
class NativeDieAccess {
public:
    struct Summary {std::uint64_t occupancy,history,version;
        bool operator==(const Summary& s)const{return std::tie(occupancy,history,version)==std::tie(s.occupancy,s.history,s.version);}};
    struct Metrics {std::uint64_t owned_reads=0,requests=0,cache_hits=0,validations=0;};
private:
    const NativeRouteState& state_;
    std::shared_ptr<const unsigned char> revision_;
    std::uint32_t net_,dies_;
    std::uint64_t present_;
    std::array<std::map<std::uint32_t,Summary>,8> reads_;
    std::array<Metrics,8> metrics_{};
    static void require(bool ok,const char* why){if(!ok)throw std::logic_error(why);}
    Summary request(std::uint32_t owner,std::uint32_t node)const{
        const auto u=state_.owner_use(owner,node);
        return u?Summary{u->nets.size(),u->history,u->version}:Summary{0,0,0};
    }
    std::uint64_t cost_value(Summary s,bool own)const{
        const auto others=s.occupancy-(own&&s.occupancy?1:0);
        if(s.history>=UINT64_MAX-1||(others&&present_>(UINT64_MAX-2-s.history)/others))throw std::overflow_error("native worker cost overflow");
        return 1+s.history+present_*others;
    }
public:
    NativeDieAccess(const NativeRouteState& state,std::uint32_t net,std::uint64_t present)
        :state_(state),revision_(state.revision()),net_(net),dies_(state.owner_count()),present_(present){
        require(state.trees().count(net),"unknown native worker net");
    }
    std::uint64_t cost(std::uint32_t die,std::uint32_t node,std::uint32_t membership){
        require(die<dies_&&membership&&membership<(1u<<dies_)&&(membership&(1u<<die)),"worker touched nonlocal resource");
        require(membership==state_.layout().membership(node),"worker topology/authority disagreement");
        const auto owner=state_.owner(node);require(membership&(1u<<owner),"worker owner/membership disagreement");
        if(owner==die){++metrics_[die].owned_reads;const auto u=state_.owner_use(die,node);
            return u?cost_value({u->nets.size(),u->history,u->version},u->nets.count(net_)):1;}
        require(membership&(membership-1),"remote interior read denied");
        auto found=reads_[die].find(node);
        if(found==reads_[die].end()){const auto summary=request(owner,node);found=reads_[die].emplace(node,summary).first;++metrics_[die].requests;}
        else ++metrics_[die].cache_hits;
        return cost_value(found->second,state_.tree(net_).nodes.count(node));
    }
    bool validate(){
        bool valid=revision_==state_.revision();
        for(std::uint32_t die=0;die<dies_;++die)for(const auto& [n,s]:reads_[die]){
            ++metrics_[die].validations;valid&=s==request(state_.owner(n),n);
        }
        return valid;
    }
    const Metrics& metrics(std::uint32_t die)const{require(die<dies_,"worker metrics range");return metrics_[die];}
    template<class Emit>void observations(Emit emit)const{
        for(std::uint32_t die=0;die<dies_;++die)for(const auto& [n,s]:reads_[die])emit(die,state_.owner(n),n,s);
    }
};
}
