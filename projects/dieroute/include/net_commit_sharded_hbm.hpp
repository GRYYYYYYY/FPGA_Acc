#pragma once
#include "net_commit_hbm.hpp"
namespace dieroute {
// Three independent physical owner ports. Logical indexed-record ABI and
// exclusive transactional publication are unchanged; supports at most3 dies.
extern "C" void dieroute_net_commit_sharded_hbm(
 const SummaryWord* command,const std::uint64_t* policy,const std::uint64_t* offsets,const std::uint64_t* arcs,
 const std::uint64_t* reads,const SummaryWord* shadows,const SummaryWord* branches,const std::uint64_t* paths,
 SummaryWord* resources0,SummaryWord* resources1,SummaryWord* resources2,SummaryWord* trees,SummaryWord* nets,SummaryWord* control,SummaryWord* scratch,
 SummaryWord* deltas,SummaryWord* completion,
 std::uint32_t node_count,std::uint64_t arc_count,std::uint32_t dies,std::uint32_t shard_capacity,
 std::uint32_t net_capacity,std::uint32_t tree_capacity,std::uint32_t read_capacity,std::uint32_t shadow_capacity,
 std::uint32_t branch_capacity,std::uint32_t path_capacity,std::uint32_t scratch_capacity,std::uint32_t delta_capacity);
}
