#pragma once
#include "native_search_hbm_label_ops.hpp"
namespace dieroute {
enum class NativeFrontierStatus {current,skipped,empty,invalid,overflow};
// Exclusive worker handoff. Stale/closed entries are consumed, matching the
// reference pop loop. Invalid metadata and version exhaustion preserve both
// buffers. This component does not expand edges or commit routing authority.
template<std::uint32_t Maximum>
NativeFrontierStatus native_search_take_frontier(NativeSearchLabelSlot* labels,std::uint32_t label_capacity,
 NativeSearchQueueEntry* queue,std::uint32_t queue_capacity,std::uint32_t& count,
 std::uint64_t epoch,NativeSearchLabelSlot& output){
 if(!queue_capacity||queue_capacity>Maximum||count>queue_capacity||!label_capacity||label_capacity>Maximum||!epoch)return NativeFrontierStatus::invalid;
 if(!count)return NativeFrontierStatus::empty;
 const auto entry=queue[0];auto location=native_search_label_lookup<Maximum>(labels,label_capacity,epoch,entry.node);
 if(location.status!=NativeLabelLookup::found)return NativeFrontierStatus::invalid;
 auto value=labels[location.slot];
 const bool skip=(value.flags&1)||value.cost!=entry.cost||value.hops!=entry.hops;
 if(!skip&&value.version==UINT64_MAX)return NativeFrontierStatus::overflow;
 const auto last=queue[count-1];const auto remaining=count-1;
 if(remaining){std::uint32_t index=0;while(index<remaining/2){auto child=index*2+1;if(child+1<remaining&&native_search_queue_less(queue[child+1],queue[child]))++child;if(!native_search_queue_less(queue[child],last))break;queue[index]=queue[child];index=child;}queue[index]=last;}
 count=remaining;
 if(skip)return NativeFrontierStatus::skipped;
 value.flags|=1;++value.version;labels[location.slot]=value;output=value;return NativeFrontierStatus::current;
}
}
