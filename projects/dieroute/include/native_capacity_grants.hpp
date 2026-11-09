#pragma once
#include <cstdint>
#include <limits>
#include <map>
#include <set>
#include <vector>

namespace dieroute {
// Coordinator prototype for native electrical-node grants. Sole committed
// occupancy remains in the net authority; only tentative net holds live here.
// Serialize acquire/validate, authority commit and release through the same
// arbiter. This class alone does not make an external authority concurrent.
struct NativeGrantObservation {
    std::uint64_t version=0;
    std::uint32_t capacity=1;
    std::set<std::uint32_t> nets;
};
enum class NativeGrantStatus {granted,valid,released,invalid,capacity,stale,missing,exhausted};
struct NativeGrantResult {NativeGrantStatus status;std::uint64_t handle=0;};
class NativeCapacityGrants {
    struct Grant {
        std::uint32_t net;
        std::map<std::uint32_t,std::uint64_t> versions;
    };
    std::map<std::uint64_t,Grant> grants_;
    std::map<std::uint32_t,std::map<std::uint32_t,std::uint64_t>> holds_;
    std::uint64_t next_=1;
public:
    std::size_t active()const{return grants_.size();}
    // observe reads committed distinct-net ownership and version under the
    // arbiter; requests must be the complete canonical SLL resource union.
    template<class Observe>
    NativeGrantResult acquire(std::uint32_t net,const std::vector<std::uint32_t>& resources,Observe observe){
        if(net==UINT32_MAX||resources.empty())return {NativeGrantStatus::invalid};
        if(next_==UINT64_MAX)return {NativeGrantStatus::exhausted};
        Grant grant{net,{}};std::uint32_t previous=0;bool first=true;
        for(auto node:resources){
            if(node==UINT32_MAX||(!first&&node<=previous))return {NativeGrantStatus::invalid};
            first=false;previous=node;
        }
        for(auto node:resources){
            auto committed=observe(node);
            if(!committed.capacity||committed.nets.count(UINT32_MAX))return {NativeGrantStatus::invalid};
            auto nets=committed.nets;auto it=holds_.find(node);
            if(it!=holds_.end())for(const auto& hold:it->second)nets.insert(hold.first);
            nets.insert(net);if(nets.size()>committed.capacity)return {NativeGrantStatus::capacity};
            grant.versions.emplace(node,committed.version);
        }
        // Copy before any mutation: allocation failure leaves all holds intact.
        auto holds=holds_;auto grants=grants_;
        for(auto node:resources)++holds[node][net];
        grants.emplace(next_,std::move(grant));holds_.swap(holds);grants_.swap(grants);
        return {NativeGrantStatus::granted,next_++};
    }
    template<class Observe>
    NativeGrantStatus validate(std::uint64_t handle,std::uint32_t net,Observe observe)const{
        auto it=grants_.find(handle);if(it==grants_.end()||it->second.net!=net)return NativeGrantStatus::missing;
        for(const auto& resource:it->second.versions){
            auto committed=observe(resource.first);if(committed.version!=resource.second)return NativeGrantStatus::stale;
            auto nets=committed.nets;auto h=holds_.find(resource.first);
            if(h==holds_.end()||!h->second.count(net))return NativeGrantStatus::invalid;
            for(const auto& hold:h->second)nets.insert(hold.first);
            if(!committed.capacity||nets.size()>committed.capacity)return NativeGrantStatus::capacity;
        }
        return NativeGrantStatus::valid;
    }
    NativeGrantStatus release(std::uint64_t handle,std::uint32_t net){
        auto it=grants_.find(handle);if(it==grants_.end()||it->second.net!=net)return NativeGrantStatus::missing;
        for(const auto& resource:it->second.versions){
            auto node=holds_.find(resource.first);auto hold=node->second.find(net);
            if(!--hold->second)node->second.erase(hold);
            if(node->second.empty())holds_.erase(node);
        }
        grants_.erase(it);return NativeGrantStatus::released;
    }
};
}
