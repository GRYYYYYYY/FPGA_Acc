#pragma once
#include <cstdint>
#include <set>
#include <stdexcept>
#include <utility>
#include <vector>

namespace dieroute {
// Fixed simple die sequence, canonical electrical IDs, no virtual transition
// edges. Internal boundary nodes must enter on the earlier die and leave on
// the next die. This is an exact edge filter for this corridor family when
// available boundary resources have exactly two memberships (the U280 graph).
// It is not an oracle over alternative die orders or routes with die reentry.
class NativeMonotonePolicy {
    std::vector<std::uint32_t> dies_;
    std::set<std::uint32_t> roots_;
    std::uint32_t sink_;
public:
    NativeMonotonePolicy(std::vector<std::uint32_t> dies,const std::vector<std::uint32_t>& roots,std::uint32_t sink)
        :dies_(std::move(dies)),roots_(roots.begin(),roots.end()),sink_(sink){
        if(dies_.empty())throw std::invalid_argument("empty monotone die sequence");
        std::set<std::uint32_t> seen;
        for(auto die:dies_)if(die>=8||!seen.insert(die).second)throw std::invalid_argument("non-simple monotone die sequence");
    }
    static bool boundary(std::uint32_t mask){return mask&&(mask&(mask-1));}
    static void check_boundary(std::uint32_t mask){
        const auto rest=mask&(mask-1);
        if(rest&&(rest&(rest-1)))throw std::invalid_argument("joint portal search requires at most two SLR memberships");
    }
    // For an internal boundary, return the earlier stage of its transition.
    std::uint32_t transition(std::uint32_t mask)const{
        check_boundary(mask);
        if(!boundary(mask))return UINT32_MAX;
        for(std::size_t i=0;i+1<dies_.size();++i)
            if((mask&(1U<<dies_[i]))&&(mask&(1U<<dies_[i+1])))return std::uint32_t(i);
        return UINT32_MAX;
    }
    std::uint32_t departure(std::uint32_t node,std::uint32_t mask)const{
        check_boundary(mask);
        if(roots_.count(node))return mask&(1U<<dies_.front())?dies_.front():UINT32_MAX;
        if(boundary(mask)){auto stage=transition(mask);return stage==UINT32_MAX?UINT32_MAX:dies_[stage+1];}
        for(auto die:dies_)if(mask==(1U<<die))return die;
        return UINT32_MAX;
    }
    bool arrival(std::uint32_t node,std::uint32_t mask,std::uint32_t die)const{
        check_boundary(mask);
        if(die>=8||!(mask&(1U<<die))||roots_.count(node))return false;
        if(node==sink_){
            if(!(mask&(1U<<dies_.back())))return false;
            // The sink itself can be the last zero-hop transition. It need
            // not have an outgoing PIP on its designated destination die.
            return die==dies_.back()||(dies_.size()>1&&die==dies_[dies_.size()-2]);
        }
        if(boundary(mask)){auto stage=transition(mask);return stage!=UINT32_MAX&&die==dies_[stage];}
        for(auto d:dies_)if(d==die&&mask==(1U<<die))return true;
        return false;
    }
    bool edge(std::uint32_t src,std::uint32_t dst,std::uint32_t src_mask,std::uint32_t dst_mask,std::uint32_t pip_die)const{
        return pip_die<8&&(src_mask&dst_mask&(1U<<pip_die))&&departure(src,src_mask)==pip_die&&arrival(dst,dst_mask,pip_die);
    }
};
} // namespace dieroute
