#pragma once
#include "direct_path.hpp"
#include "path_transaction.hpp"
namespace routecast {
// All buffers must be disjoint and valid for their declared lengths. targets
// are dense ranks, not raw IDs. Termination is authoritative search evidence;
// 'reached' refers to final settled state. Unknown failures bypass commit.
// Only staged workspace changes before commit; accepted buffers/counts survive
// every failure. This does not update resource demand or connection epochs.
inline QueryStatus direct_commit_paths(SearchTermination termination,uint64_t root,uint64_t nodes,const uint64_t* targets,
 uint64_t target_count,const SearchLabel* labels,const uint8_t* settled,
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
 for(uint64_t i=0;i<target_count;++i){if(targets[i]>=nodes)return QueryStatus::invalid_input;if(!settled[targets[i]])return termination==SearchTermination::frontier_empty?QueryStatus::unreachable:QueryStatus::invalid_input;}
 uint64_t used=0;staged_offsets[0]=0;
 for(uint64_t i=0;i<target_count;++i){
  uint64_t length=0;
  auto status=direct_reverse_path(targets[i],root,nodes,labels,scratch,scratch_capacity,length);
  if(status==PathStatus::invalid_parent)return QueryStatus::invalid_input;
  if(status==PathStatus::capacity)return QueryStatus::path_capacity;
  if(length>staged_capacity-used)return QueryStatus::path_capacity;
  for(uint64_t j=0;j<length;++j)staged_edges[used+j]=scratch[length-1-j];
  used+=length;staged_offsets[i+1]=used;
 }
 if(used>accepted_capacity)return QueryStatus::path_capacity;
 for(uint64_t i=0;i<used;++i)accepted_edges[i]=staged_edges[i];
 for(uint64_t i=0;i<=target_count;++i)accepted_offsets[i]=staged_offsets[i];
 accepted_edge_count=used;accepted_target_count=target_count;
 return QueryStatus::complete;
}
}
