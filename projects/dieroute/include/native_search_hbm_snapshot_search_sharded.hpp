#pragma once
#include "native_search_hbm_snapshot_search.hpp"
#include "native_search_hbm_resource_sharded.hpp"
namespace dieroute {
// Single-worker, one-shot scratch search under an exclusive immutable authority
// handoff. Caller seeds every node of the current net tree, supplies its exact
// absolute depths, local label credit count and an epoch not previously reused.
// Thus every nonroot observation is foreign-net occupancy (own=false).
// Potential, if supplied, must be consistent, nonnegative and zero at the sink.
// Budget/failure requires a fresh epoch; no resumable search or async snapshot
// protocol is implied. Authority is read-only; route publication is separate.
template<std::uint32_t MaximumNodes,std::uint64_t MaximumArcs,std::uint32_t MaximumEntries,std::uint32_t MaximumShard>
NativeSnapshotResult native_search_snapshot_sharded(const std::uint64_t* offsets,const std::uint64_t* arcs,
 const std::uint64_t* policy,const SummaryWord* resources0,const SummaryWord* resources1,const SummaryWord* resources2,const SummaryWord& control,
 const std::uint64_t* potential,NativeSearchLabelSlot* labels,std::uint32_t label_capacity,
 NativeSearchQueueEntry* queue,std::uint32_t queue_capacity,std::uint32_t& queued,
 NativeSearchResourceObservation* journal,std::uint32_t journal_capacity,std::uint32_t& used,
 std::uint32_t& touched,std::uint32_t nodes,std::uint64_t arc_count,std::uint32_t dies,
 std::uint32_t shard_capacity,std::uint32_t tree_capacity,std::uint32_t net,std::uint32_t sink,
 std::uint64_t session,std::uint64_t revision,std::uint64_t epoch,std::uint64_t expansion_limit,
 std::uint32_t max_hops){
 NativeSnapshotResult result{};
 if(!nodes||nodes>MaximumNodes||sink>=nodes||net==UINT32_MAX||arc_count>MaximumArcs||
    !dies||dies>3||!shard_capacity||shard_capacity>MaximumShard||(shard_capacity&(shard_capacity-1))||
    !tree_capacity||!session||!epoch||!label_capacity||label_capacity>MaximumEntries||
    !queue_capacity||queue_capacity>MaximumEntries||queued>queue_capacity||!journal_capacity||
    journal_capacity>MaximumEntries||used>journal_capacity||touched>label_capacity||
    control.w[0]!=session||control.w[1]!=revision||control.w[5]!=(nodes|(std::uint64_t(dies)<<32))||
    std::uint32_t(control.w[6])!=shard_capacity||control.w[7]!=tree_capacity||(potential&&potential[sink]))return result;
 bool hop_cutoff=false;
 while(queued){
  auto head=queue[0];auto location=native_search_label_lookup<MaximumEntries>(labels,label_capacity,epoch,head.node);
  if(location.status!=NativeLabelLookup::found)return result;
  const auto old=labels[location.slot];
  if(!(old.flags&1)&&old.cost==head.cost&&old.hops==head.hops&&result.expanded>=expansion_limit){result.status=NativeSnapshotStatus::budget;return result;}
  NativeSearchLabelSlot current{};auto popped=native_search_take_frontier<MaximumEntries>(labels,label_capacity,queue,queue_capacity,queued,epoch,current);
  if(popped==NativeFrontierStatus::skipped)continue;
  if(popped!=NativeFrontierStatus::current){result.status=popped==NativeFrontierStatus::overflow?NativeSnapshotStatus::overflow:NativeSnapshotStatus::invalid;return result;}
  ++result.expanded;
  if(current.node==sink){result.status=NativeSnapshotStatus::found;result.goal=current;return result;}
  if(current.hops>=max_hops){hop_cutoff=true;continue;}
  if(current.hops>=UINT32_MAX-1)return result;
  if(current.node>=nodes)return result;
  auto cursor=offsets[current.node];
  while(true){
   std::uint64_t visits=0;NativeCSRArc arc{};
   auto scan=native_search_next_arc<MaximumNodes,MaximumArcs>(offsets,arcs,policy,nodes,arc_count,dies,current.node,net,64,cursor,visits,arc);
   if(scan==NativeCSRStatus::invalid)return result;
   result.raw_arcs+=visits;
   if(scan==NativeCSRStatus::end)break;
   if(scan==NativeCSRStatus::budget)continue;
   ++result.edge_visits;
   auto previous=native_search_label_lookup<MaximumEntries>(labels,label_capacity,epoch,arc.node);
   if(previous.status==NativeLabelLookup::invalid)return result;
   const bool present=previous.status==NativeLabelLookup::found;
   if(present&&(labels[previous.slot].flags&3))continue;
   if(used==journal_capacity){result.status=NativeSnapshotStatus::journal_full;return result;}
   NativeSearchResourceObservation observation{};
   auto read=native_search_read_resource_sharded<MaximumShard>(policy,resources0,resources1,resources2,control,nodes,dies,shard_capacity,tree_capacity,arc.node,session,revision,epoch,observation);
   if(read==NativeResourceReadStatus::invalid)return result;
   auto status=native_search_relax_observed<MaximumEntries>(labels,label_capacity,queue,queue_capacity,queued,current,arc.node,arc.edge,observation,session,journal,journal_capacity,used,false,control.w[2],potential?potential[arc.node]:0,UINT64_MAX,touched<label_capacity);
   if(status==NativeObservedRelaxStatus::accepted){if(!present)++touched;continue;}
   if(status==NativeObservedRelaxStatus::dominated||status==NativeObservedRelaxStatus::unreachable)continue;
   if(status==NativeObservedRelaxStatus::label_capacity||status==NativeObservedRelaxStatus::queue_capacity)result.status=NativeSnapshotStatus::budget;
   else if(status==NativeObservedRelaxStatus::journal_full)result.status=NativeSnapshotStatus::journal_full;
   else if(status==NativeObservedRelaxStatus::cost_overflow||status==NativeObservedRelaxStatus::version_overflow)result.status=NativeSnapshotStatus::overflow;
   return result;
  }
 }
 result.status=hop_cutoff?NativeSnapshotStatus::hop_limited:NativeSnapshotStatus::exhausted;return result;
}
}
