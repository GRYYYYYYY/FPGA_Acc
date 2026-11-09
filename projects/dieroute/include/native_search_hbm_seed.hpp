#pragma once
#include "native_search_hbm_labels.hpp"
#include "native_search_hbm_queue.hpp"
namespace dieroute {
enum class NativeSeedStatus {accepted,unchanged,invalid,label_capacity,queue_capacity,overflow,unreachable,cost_limited};
// Initialization phase only, with exclusive table/queue access. Coordinator
// owns epoch/reset and new-label credit. Rejection preserves all storage.
template<std::uint32_t Maximum>
NativeSeedStatus native_search_seed(NativeSearchLabelSlot* labels,std::uint32_t capacity,
 NativeSearchQueueEntry* queue,std::uint32_t queue_capacity,std::uint32_t& queued,
 const NativeSearchLabelSlot& seed,std::uint64_t potential,std::uint64_t max_cost,bool credit,
 NativeSearchLabelSlot& output){
 if(!queue_capacity||queue_capacity>Maximum||queued>queue_capacity||!seed.epoch||seed.node==UINT32_MAX||seed.cost==UINT64_MAX||seed.hops==UINT32_MAX)return NativeSeedStatus::invalid;
 if(potential==UINT64_MAX)return NativeSeedStatus::unreachable;
 if(potential>=UINT64_MAX-seed.cost)return NativeSeedStatus::overflow;
 if(seed.cost+potential>max_cost)return NativeSeedStatus::cost_limited;
 auto loc=native_search_label_lookup<Maximum>(labels,capacity,seed.epoch,seed.node);
 if(loc.status==NativeLabelLookup::invalid)return NativeSeedStatus::invalid;
 if(loc.status==NativeLabelLookup::full)return NativeSeedStatus::label_capacity;
 bool created=loc.status==NativeLabelLookup::missing;auto old=created?NativeSearchLabelSlot{}:labels[loc.slot];
 if(old.flags&1)return NativeSeedStatus::invalid;
 if(seed.cost>old.cost||(seed.cost==old.cost&&seed.hops>=old.hops))return NativeSeedStatus::unchanged;
 if(created&&!credit)return NativeSeedStatus::label_capacity;
 if(old.version==UINT64_MAX)return NativeSeedStatus::overflow;
 if(queued==queue_capacity)return NativeSeedStatus::queue_capacity;
 NativeSearchQueueEntry entry{seed.cost+potential,seed.cost,seed.hops,seed.node,UINT32_MAX};auto index=queued;
 while(index){auto parent=(index-1)/2;if(!native_search_queue_less(entry,queue[parent]))break;queue[index]=queue[parent];index=parent;}
 queue[index]=entry;++queued;
 output={seed.epoch,seed.cost,old.version+1,seed.node,seed.hops,UINT32_MAX,UINT32_MAX,2};labels[loc.slot]=output;return NativeSeedStatus::accepted;
}
}
