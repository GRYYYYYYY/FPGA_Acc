#pragma once
#include "native_search_hbm_observation.hpp"
namespace dieroute {
enum class NativeSummaryBindingStatus {ok,invalid};
// Bind an already-delivered summary packet to the expected topology and ticket.
// The packet carries session, not search epoch: epoch comes from the caller's
// exclusive snapshot/handoff and is not independently proved by this decoder.
// This validates fields; it does not authenticate DMA provenance or freshness.
inline NativeSummaryBindingStatus native_search_bind_summary(
 const std::uint64_t* words,std::uint32_t node,std::uint32_t owner,
 std::uint32_t worker,std::uint32_t membership,std::uint64_t serial,
 std::uint64_t session,std::uint64_t epoch,NativeSearchResourceObservation& output){
 if(node==UINT32_MAX||owner>=8||worker>=8||owner==worker||!membership||membership>255||
    !(membership&(1u<<worker))||!(membership&(1u<<owner))||
    (membership&(~membership+1u))!=(1u<<owner)||!serial||!session||!epoch)
  return NativeSummaryBindingStatus::invalid;
 const auto descriptor=words[1];const auto kind=(descriptor>>48)&255;
 if(words[0]!=session||std::uint32_t(descriptor)!=node||((descriptor>>32)&255)!=owner||
    ((descriptor>>40)&255)!=worker||(kind!=2&&kind!=3)||descriptor>>56||
    words[5]!=serial||words[6]||words[7]||words[3]==UINT64_MAX)
  return NativeSummaryBindingStatus::invalid;
 output={node,words[4],words[2],words[3],session,epoch,owner,0};
 return NativeSummaryBindingStatus::ok;
}
template<std::uint32_t Maximum>
NativeSearchObservationStatus native_search_observe_summary(
 const std::uint64_t* words,std::uint32_t node,std::uint32_t owner,std::uint32_t worker,
 std::uint32_t membership,std::uint64_t serial,std::uint64_t session,std::uint64_t epoch,
 NativeSearchResourceObservation* journal,std::uint32_t capacity,std::uint32_t& used,
 bool own,std::uint64_t present,std::uint64_t& cost){
 NativeSearchResourceObservation value{};
 if(native_search_bind_summary(words,node,owner,worker,membership,serial,session,epoch,value)!=NativeSummaryBindingStatus::ok)
  return NativeSearchObservationStatus::invalid;
 return native_search_observe_cost<Maximum>(value,node,session,epoch,journal,capacity,used,own,present,cost);
}
}
