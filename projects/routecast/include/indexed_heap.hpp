#pragma once
#include <cstdint>
// Caller-owned storage. IDs are dense node ranks; comparator reads stable labels.
// No allocation, stale entries, or implicit eviction. Failed insert is atomic.
namespace routecast {
constexpr uint64_t no_position=UINT64_MAX;
enum class HeapStatus { ok, invalid_rank, capacity };
template<class Less> struct IndexedHeap {
 uint64_t* entries;uint64_t* positions;uint64_t nodes,capacity,size;Less less;
 IndexedHeap(uint64_t* e,uint64_t* p,uint64_t n,uint64_t c,Less l):entries(e),positions(p),nodes(n),capacity(c),size(0),less(l){for(uint64_t i=0;i<n;++i)positions[i]=no_position;}
 void swap(uint64_t a,uint64_t b){uint64_t t=entries[a];entries[a]=entries[b];entries[b]=t;positions[entries[a]]=a;positions[entries[b]]=b;}
 HeapStatus decrease_or_insert(uint64_t node){
  if(node>=nodes)return HeapStatus::invalid_rank;
  uint64_t i=positions[node];
  if(i==no_position){if(size==capacity)return HeapStatus::capacity;i=size++;entries[i]=node;positions[node]=i;}
  // Existing label must only decrease; caller owns that invariant.
  while(i){uint64_t parent=(i-1)/2;if(!less(entries[i],entries[parent]))break;swap(i,parent);i=parent;}
  return HeapStatus::ok;
 }
 bool pop(uint64_t& node){
  if(!size)return false;
  node=entries[0];positions[node]=no_position;--size;
  if(size){entries[0]=entries[size];positions[entries[0]]=0;uint64_t i=0;
   while(i<=(size-1)/2){uint64_t child=2*i+1;if(child>=size)break;if(child+1<size&&less(entries[child+1],entries[child]))++child;if(!less(entries[child],entries[i]))break;swap(i,child);i=child;}
  }
  return true;
 }
};
}
