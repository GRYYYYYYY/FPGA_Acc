#pragma once
#include "native_search_hbm_labels.hpp"
#include "native_search_hbm_queue.hpp"
namespace dieroute {
enum class NativeSearchAdmission {accepted,invalid,stale,protected_label,dominated,label_capacity,queue_capacity,overflow};
struct alignas(64) NativeSearchRelaxation {
    std::uint64_t epoch,observed_version,priority,cost;
    std::uint32_t node,hops,parent,edge;
    std::uint32_t reserved[4]{};
};
// Exclusive access to label and queue buffers is required through completion.
// Global new-label credit is supplied by the coordinator; this component does
// not implement concurrent admission, authority commit or crash atomicity.
template<std::uint32_t Maximum>
NativeSearchAdmission native_search_admit(NativeSearchLabelSlot* labels,std::uint32_t label_capacity,
    NativeSearchQueueEntry* queue,std::uint32_t queue_capacity,std::uint32_t& queued,
    const NativeSearchRelaxation& request,bool new_label_credit){
    if(!label_capacity||label_capacity>Maximum||!queue_capacity||queue_capacity>Maximum||queued>queue_capacity||
       !request.epoch||request.node==UINT32_MAX||request.parent==UINT32_MAX||!request.hops||
       request.cost==UINT64_MAX||request.priority==UINT64_MAX||request.priority<request.cost)
        return NativeSearchAdmission::invalid;
    for(unsigned i=0;i<4;++i)if(request.reserved[i])return NativeSearchAdmission::invalid;
    auto location=native_search_label_lookup<Maximum>(labels,label_capacity,request.epoch,request.node);
    if(location.status==NativeLabelLookup::invalid)return NativeSearchAdmission::invalid;
    if(location.status==NativeLabelLookup::full)return NativeSearchAdmission::label_capacity;
    const bool created=location.status==NativeLabelLookup::missing;
    NativeSearchLabelSlot old=created?NativeSearchLabelSlot{}:labels[location.slot];
    if(old.version!=request.observed_version)return NativeSearchAdmission::stale;
    if(old.flags&3)return NativeSearchAdmission::protected_label;
    bool improves=request.cost<old.cost;
    if(request.cost==old.cost){
        improves=request.hops<old.hops;
        if(request.hops==old.hops){improves=request.parent<old.parent;if(request.parent==old.parent)improves=request.edge<old.edge;}
    }
    if(!improves)return NativeSearchAdmission::dominated;
    if(created&&!new_label_credit)return NativeSearchAdmission::label_capacity;
    if(old.version==UINT64_MAX)return NativeSearchAdmission::overflow;
    if(queued==queue_capacity)return NativeSearchAdmission::queue_capacity;
    // All rejection conditions are checked before the first storage write.
    NativeSearchQueueEntry entry{request.priority,request.cost,request.hops,request.node,request.parent};
    auto index=queued;
    while(index){auto parent=(index-1)/2;if(!native_search_queue_less(entry,queue[parent]))break;queue[index]=queue[parent];index=parent;}
    queue[index]=entry;++queued;
    labels[location.slot]={request.epoch,request.cost,old.version+1,request.node,request.hops,request.parent,request.edge,0};
    return NativeSearchAdmission::accepted;
}
}
