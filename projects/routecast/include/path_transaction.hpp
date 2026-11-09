#pragma once
#include "predecessor_path.hpp"
namespace routecast {
enum class QueryStatus { complete, unreachable, invalid_input, path_capacity, work_budget, frontier_capacity, unsupported_context };
enum class SearchTermination { targets_complete, frontier_empty, work_budget, frontier_capacity, path_capacity, invalid_input, unsupported_context };
// All buffers must be disjoint and valid for their declared lengths. targets
// are dense ranks, not raw IDs. Termination is authoritative search evidence;
// 'reached' refers to final settled state. Unknown failures bypass commit.
// Only staged workspace changes before commit; accepted buffers/counts survive
// every failure. This does not update resource demand or connection epochs.
template<class Parent,class Edge,class Reached>
QueryStatus commit_paths(SearchTermination termination,uint64_t root,uint64_t nodes,const uint64_t* targets,
 uint64_t target_count,Parent parent,Edge edge,Reached reached,
 uint64_t* scratch,uint64_t scratch_capacity,
 uint64_t* staged_edges,uint64_t staged_capacity,
 uint64_t* staged_offsets,uint64_t staged_offset_capacity,
 uint64_t* accepted_edges,uint64_t accepted_capacity,
 uint64_t* accepted_offsets,uint64_t accepted_offset_capacity,
 uint64_t& accepted_edge_count,uint64_t& accepted_target_count){
 switch(termination){
 case SearchTermination::work_budget:return QueryStatus::work_budget;
 case SearchTermination::frontier_capacity:return QueryStatus::frontier_capacity;
 case SearchTermination::path_capacity:return QueryStatus::path_capacity;
 case SearchTermination::invalid_input:return QueryStatus::invalid_input;
 case SearchTermination::unsupported_context:return QueryStatus::unsupported_context;
 case SearchTermination::targets_complete:case SearchTermination::frontier_empty:break;
 default:return QueryStatus::invalid_input;
 }
 if(root>=nodes)return QueryStatus::invalid_input;
 // Avoid count+1 overflow. Offsets include final sentinel.
 if(target_count>=staged_offset_capacity||target_count>=accepted_offset_capacity)return QueryStatus::path_capacity;
 for(uint64_t i=0;i<target_count;++i){if(targets[i]>=nodes)return QueryStatus::invalid_input;if(!reached(targets[i]))return termination==SearchTermination::frontier_empty?QueryStatus::unreachable:QueryStatus::invalid_input;}
 uint64_t used=0;staged_offsets[0]=0;
 for(uint64_t i=0;i<target_count;++i){
  uint64_t length=0;
  auto status=reconstruct_path(targets[i],root,nodes,parent,edge,scratch,scratch_capacity,staged_edges+used,staged_capacity-used,length);
  if(status==PathStatus::invalid_parent)return QueryStatus::invalid_input;
  if(status==PathStatus::capacity)return QueryStatus::path_capacity;
  used+=length;staged_offsets[i+1]=used;
 }
 if(used>accepted_capacity)return QueryStatus::path_capacity;
 for(uint64_t i=0;i<used;++i)accepted_edges[i]=staged_edges[i];
 for(uint64_t i=0;i<=target_count;++i)accepted_offsets[i]=staged_offsets[i];
 accepted_edge_count=used;accepted_target_count=target_count;
 return QueryStatus::complete;
}
}
