#pragma once
#include "workspace_search.hpp"
// Flat pointer ABI candidate; host authenticates immutable graph/cost context.
// All work/staging/accepted regions are disjoint. No final AXI mapping yet.
extern "C" uint8_t routecast_workspace_flat(
 const uint64_t* rows,const uint64_t* edge_ids,const uint64_t* destinations,
 const uint64_t* costs,const uint64_t* capacities,const uint8_t* types,
 uint64_t nodes,uint64_t edges,uint64_t source,const uint64_t* targets,
 uint64_t target_count,uint64_t work_budget,uint8_t context_verified,
 routecast::SearchLabel* labels,uint8_t* known,uint8_t* settled,
 uint64_t* positions,uint64_t* frontier,uint64_t* scratch,uint64_t* left,
 uint64_t* right,uint64_t node_capacity,uint64_t frontier_capacity,uint64_t path_capacity,
 uint64_t* staged_edges,uint64_t staged_capacity,uint64_t* staged_offsets,uint64_t staged_offset_capacity,
 uint64_t* accepted_edges,uint64_t accepted_capacity,uint64_t* accepted_offsets,uint64_t accepted_offset_capacity,
 uint64_t& accepted_edge_count,uint64_t& accepted_target_count,routecast::SearchCounters& counters);
