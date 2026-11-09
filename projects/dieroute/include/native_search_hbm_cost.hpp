#pragma once
#include <cstdint>
namespace dieroute {
enum class NativeSearchCostStatus {ok,overflow};
// Exact native negotiated cost from an owner/shadow observation. Static policy
// and protected-label checks happen before obtaining the observation; every
// actual dynamic observation must be journalled even if its arc is not chosen.
inline NativeSearchCostStatus native_search_observed_cost(std::uint64_t occupancy,
 std::uint64_t history,bool own,std::uint64_t present,std::uint64_t& output){
 const auto others=occupancy-(own&&occupancy?1:0);
 if(history>=UINT64_MAX-1||(others&&present>(UINT64_MAX-2-history)/others))return NativeSearchCostStatus::overflow;
 output=1+history+present*others;return NativeSearchCostStatus::ok;
}
struct alignas(64) NativeSearchResourceObservation {
 std::uint64_t node,version,occupancy,history,session,epoch,owner,reserved;
};
}
