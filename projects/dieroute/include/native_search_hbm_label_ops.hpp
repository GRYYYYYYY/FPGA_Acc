#pragma once
#include "native_search_hbm_labels.hpp"
#include "native_search_hbm_queue.hpp"
namespace dieroute {
enum class NativeSearchLabelOpStatus {ok,missing,invalid,stale,closed,overflow};
// Read-only traceback/probe. Rejection preserves output. Table storage is
// exclusively owned by one worker; epoch monotonicity is enforced externally.
template<std::uint32_t Maximum>
NativeSearchLabelOpStatus native_search_label_read(const NativeSearchLabelSlot* labels,
    std::uint32_t capacity,std::uint64_t epoch,std::uint32_t node,NativeSearchLabelSlot& output){
    const auto found=native_search_label_lookup<Maximum>(labels,capacity,epoch,node);
    if(found.status==NativeLabelLookup::invalid)return NativeSearchLabelOpStatus::invalid;
    if(found.status!=NativeLabelLookup::found)return NativeSearchLabelOpStatus::missing;
    output=labels[found.slot];return NativeSearchLabelOpStatus::ok;
}
// Reference search rejects stale cost/hop queue entries and already-closed
// labels before expansion. Parent changes at equal cost/hops do not discard
// an otherwise current queue entry: expansion uses the authoritative label.
template<std::uint32_t Maximum>
NativeSearchLabelOpStatus native_search_label_close(NativeSearchLabelSlot* labels,
    std::uint32_t capacity,std::uint64_t epoch,const NativeSearchQueueEntry& entry,
    NativeSearchLabelSlot& output){
    const auto found=native_search_label_lookup<Maximum>(labels,capacity,epoch,entry.node);
    if(found.status==NativeLabelLookup::invalid)return NativeSearchLabelOpStatus::invalid;
    if(found.status!=NativeLabelLookup::found)return NativeSearchLabelOpStatus::missing;
    auto value=labels[found.slot];
    if(value.flags&1)return NativeSearchLabelOpStatus::closed;
    if(value.cost!=entry.cost||value.hops!=entry.hops)return NativeSearchLabelOpStatus::stale;
    if(value.version==UINT64_MAX)return NativeSearchLabelOpStatus::overflow;
    value.flags|=1;++value.version;labels[found.slot]=value;output=value;
    return NativeSearchLabelOpStatus::ok;
}
}
