#pragma once
#include "native_search_hbm_admission.hpp"
#include "native_search_hbm_observation.hpp"
namespace dieroute {
enum class NativeObservedRelaxStatus {accepted,invalid,protected_label,journal_full,cost_overflow,dominated,unreachable,cost_limited,label_capacity,queue_capacity,stale,version_overflow};
// Serialized worker arc evaluation. Caller owns immutable parent/owner inputs,
// static arc permission and a consistent potential. This is not owner transport.
template<std::uint32_t Maximum>
NativeObservedRelaxStatus native_search_relax_observed(
 NativeSearchLabelSlot* labels,std::uint32_t label_capacity,
 NativeSearchQueueEntry* queue,std::uint32_t queue_capacity,std::uint32_t& queued,
 const NativeSearchLabelSlot& parent,std::uint32_t dst,std::uint32_t edge,
 const NativeSearchResourceObservation& observation,std::uint64_t session,
 NativeSearchResourceObservation* journal,std::uint32_t journal_capacity,std::uint32_t& used,
 bool own,std::uint64_t present,std::uint64_t potential,std::uint64_t max_cost,bool credit){
 if(!parent.epoch||parent.node==UINT32_MAX||parent.cost==UINT64_MAX||parent.hops>=UINT32_MAX-1||!(parent.flags&1)||dst==UINT32_MAX||edge==UINT32_MAX)
  return NativeObservedRelaxStatus::invalid;
 auto location=native_search_label_lookup<Maximum>(labels,label_capacity,parent.epoch,dst);
 if(location.status==NativeLabelLookup::invalid)return NativeObservedRelaxStatus::invalid;
 NativeSearchLabelSlot old{};
 if(location.status==NativeLabelLookup::found)old=labels[location.slot];
 if(old.flags&3)return NativeObservedRelaxStatus::protected_label;
 std::uint64_t delta=0;
 auto observed=native_search_observe_cost<Maximum>(observation,dst,session,parent.epoch,journal,journal_capacity,used,own,present,delta);
 if(observed==NativeSearchObservationStatus::invalid)return NativeObservedRelaxStatus::invalid;
 if(observed==NativeSearchObservationStatus::journal_full)return NativeObservedRelaxStatus::journal_full;
 if(observed==NativeSearchObservationStatus::cost_overflow||delta>=UINT64_MAX-parent.cost)return NativeObservedRelaxStatus::cost_overflow;
 const auto cost=parent.cost+delta;const auto hops=parent.hops+1;
 bool improve=cost<old.cost;
 if(cost==old.cost){improve=hops<old.hops;if(hops==old.hops){improve=parent.node<old.parent;if(parent.node==old.parent)improve=edge<old.edge;}}
 if(!improve)return NativeObservedRelaxStatus::dominated;
 if(potential==UINT64_MAX)return NativeObservedRelaxStatus::unreachable;
 if(potential>=UINT64_MAX-cost)return NativeObservedRelaxStatus::cost_overflow;
 if(cost+potential>max_cost)return NativeObservedRelaxStatus::cost_limited;
 NativeSearchRelaxation request{parent.epoch,old.version,cost+potential,cost,dst,hops,parent.node,edge};
 switch(native_search_admit<Maximum>(labels,label_capacity,queue,queue_capacity,queued,request,credit)){
 case NativeSearchAdmission::accepted:return NativeObservedRelaxStatus::accepted;
 case NativeSearchAdmission::stale:return NativeObservedRelaxStatus::stale;
 case NativeSearchAdmission::protected_label:return NativeObservedRelaxStatus::protected_label;
 case NativeSearchAdmission::dominated:return NativeObservedRelaxStatus::dominated;
 case NativeSearchAdmission::label_capacity:return NativeObservedRelaxStatus::label_capacity;
 case NativeSearchAdmission::queue_capacity:return NativeObservedRelaxStatus::queue_capacity;
 case NativeSearchAdmission::overflow:return NativeObservedRelaxStatus::version_overflow;
 default:return NativeObservedRelaxStatus::invalid;
 }
}
}
