#pragma once
#include <cstdint>
namespace dieroute {
struct alignas(64) NativeSearchLabelSlot {
    std::uint64_t epoch=0,cost=UINT64_MAX,version=0;
    std::uint32_t node=UINT32_MAX,hops=UINT32_MAX,parent=UINT32_MAX,edge=UINT32_MAX,flags=0;
    std::uint32_t reserved[5]{};
};
enum class NativeLabelLookup {found,missing,full,invalid};
struct NativeLabelLocation {NativeLabelLookup status;std::uint32_t slot;};
// Exclusive owner per search worker. Epoch reuse/wrap and global admission
// credits are controller responsibilities. Lookup never changes storage.
// Caller may write a missing slot only after queue and label credits succeed.
template<std::uint32_t Maximum>
NativeLabelLocation native_search_label_lookup(const NativeSearchLabelSlot* slots,
    std::uint32_t capacity,std::uint64_t epoch,std::uint32_t node){
    static_assert(Maximum>0,"nonzero table bound");
    if(!capacity||capacity>Maximum||!epoch||node==UINT32_MAX)return {NativeLabelLookup::invalid,UINT32_MAX};
    auto index=node%capacity;
    for(std::uint32_t probe=0;probe<capacity;++probe){
        const auto value=slots[index];
        if(value.epoch>epoch)return {NativeLabelLookup::invalid,UINT32_MAX};
        if(value.epoch!=epoch)return {NativeLabelLookup::missing,index};
        if(value.node==node)return {NativeLabelLookup::found,index};
        if(++index==capacity)index=0;
    }
    return {NativeLabelLookup::full,UINT32_MAX};
}
}
