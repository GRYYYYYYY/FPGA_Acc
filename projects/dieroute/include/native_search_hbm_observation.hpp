#pragma once
#include "native_search_hbm_cost.hpp"
namespace dieroute {
enum class NativeSearchObservationStatus {ok,invalid,journal_full,cost_overflow};
// Owner observations must remain immutable under the caller's handoff while
// this function executes. It logs values supplied by the owner data plane;
// independent dispatch/source binding is still required by integration.
// Every actual dynamic read is retained, including reads ending in overflow.
// Duplicates are intentional: later canonicalization must preserve all values.
template<std::uint32_t Maximum>
NativeSearchObservationStatus native_search_observe_cost(
 const NativeSearchResourceObservation& value,std::uint64_t expected_node,
 std::uint64_t expected_session,std::uint64_t expected_epoch,
 NativeSearchResourceObservation* journal,std::uint32_t capacity,std::uint32_t& used,
 bool own,std::uint64_t present,std::uint64_t& cost){
 if(!capacity||capacity>Maximum||used>capacity||!expected_session||!expected_epoch||
    value.node!=expected_node||value.session!=expected_session||value.epoch!=expected_epoch||value.reserved||value.owner>=8)
    return NativeSearchObservationStatus::invalid;
 if(used==capacity)return NativeSearchObservationStatus::journal_full;
 journal[used]=value;++used;
 if(native_search_observed_cost(value.occupancy,value.history,own,present,cost)!=NativeSearchCostStatus::ok)
    return NativeSearchObservationStatus::cost_overflow;
 return NativeSearchObservationStatus::ok;
}
}
