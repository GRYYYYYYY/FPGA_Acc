#pragma once
#include <cstdint>
namespace dieroute {
struct alignas(64) NativeSearchQueueEntry {
    std::uint64_t priority, cost;
    std::uint32_t hops, node, parent;
    std::uint32_t reserved[9]{};
};
inline bool native_search_queue_less(const NativeSearchQueueEntry& a,const NativeSearchQueueEntry& b){
    if(a.priority!=b.priority)return a.priority<b.priority;
    if(a.cost!=b.cost)return a.cost<b.cost;
    if(a.hops!=b.hops)return a.hops<b.hops;
    if(a.node!=b.node)return a.node<b.node;
    return a.parent<b.parent;
}
// Caller exclusively owns external storage and count during each operation.
// Capacity failure and empty pop preserve storage/count and output respectively.
// This heap is a search component, not a concurrent or crash-atomic protocol.
template<std::uint32_t Maximum> class NativeSearchHBMQueue {
    static_assert(Maximum>0&&Maximum<=UINT32_MAX/2,"nonzero maximum required");
    NativeSearchQueueEntry* entries_;
    std::uint32_t capacity_;
    std::uint32_t& count_;
public:
    NativeSearchHBMQueue(NativeSearchQueueEntry* entries,std::uint32_t capacity,std::uint32_t& count)
        :entries_(entries),capacity_(capacity),count_(count){}
    bool valid()const{return entries_&&capacity_>0&&capacity_<=Maximum&&count_<=capacity_;}
    bool push(const NativeSearchQueueEntry& entry){
        if(!valid()||count_==capacity_)return false;
        auto index=count_;
        while(index){
            const auto parent=(index-1)/2;
            if(!native_search_queue_less(entry,entries_[parent]))break;
            entries_[index]=entries_[parent];index=parent;
        }
        entries_[index]=entry;++count_;return true;
    }
    bool pop(NativeSearchQueueEntry& output){
        if(!valid()||!count_)return false;
        output=entries_[0];const auto last=entries_[count_-1];--count_;
        if(!count_)return true;
        std::uint32_t index=0;
        while(index<count_/2){
            const auto left=index*2+1;auto child=left;
            if(left+1<count_&&native_search_queue_less(entries_[left+1],entries_[left]))child=left+1;
            if(!native_search_queue_less(entries_[child],last))break;
            entries_[index]=entries_[child];index=child;
        }
        entries_[index]=last;return true;
    }
};
}
