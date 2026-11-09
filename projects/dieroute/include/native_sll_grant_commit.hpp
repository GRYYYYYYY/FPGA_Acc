#pragma once
#include "native_capacity_grants.hpp"
#include "native_net_transaction.hpp"

namespace dieroute {
inline std::vector<std::uint32_t> native_proposal_sll_union(const NativeRouteState& state,const NativeNetProposal& proposal){
    std::set<std::uint32_t> nodes;
    auto include=[&](std::uint32_t node){auto mask=state.layout().membership(node);if(mask&(mask-1))nodes.insert(node);};
    for(const auto& branch:proposal.branches)if(branch.result.status==SparseSearchStatus::found){
        include(branch.result.attachment);
        for(auto node:branch.result.path)include(node);
    }
    return {nodes.begin(),nodes.end()};
}
struct NativeStrictCommitResult {NativeGrantStatus grant_status;bool committed;};
// Caller holds the shared authority/grant arbiter across this entire call.
// commit must validate and atomically publish the full net; CPU native_commit_net
// or a future kernel adapter may supply it. The callback receives the exact
// proposal whose SLL union was granted. Never silently substitute this for
// negotiated routing: capacity denial requires explicit scheduler retry/repair.
template<class Commit>
NativeStrictCommitResult native_strict_sll_commit(NativeCapacityGrants& grants,const NativeRouteState& state,const NativeNetProposal& proposal,std::uint64_t present,Commit commit){
    if(!native_validate_net(state,proposal,present).valid())return {NativeGrantStatus::stale,false};
    auto nodes=native_proposal_sll_union(state,proposal);
    if(nodes.empty())return {NativeGrantStatus::valid,commit(proposal)};
    auto observe=[&](std::uint32_t node){
        NativeGrantObservation observation;auto use=state.find_use(node);
        if(use){observation.version=use->version;observation.nets=use->nets;}
        return observation;
    };
    auto grant=grants.acquire(proposal.net,nodes,observe);
    if(grant.status!=NativeGrantStatus::granted)return {grant.status,false};
    struct Release {NativeCapacityGrants& grants;std::uint64_t handle;std::uint32_t net;~Release(){grants.release(handle,net);}} release{grants,grant.handle,proposal.net};
    auto status=grants.validate(grant.handle,proposal.net,observe);
    if(status!=NativeGrantStatus::valid)return {status,false};
    return {status,commit(proposal)};
}
}
