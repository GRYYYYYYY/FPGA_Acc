#include "workspace_flat.hpp"
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
 uint64_t& accepted_edge_count,uint64_t& accepted_target_count,routecast::SearchCounters& counters){
 if(context_verified!=1){counters={};return uint8_t(routecast::QueryStatus::unsupported_context);}
 routecast::PreparedSearchGraph graph{rows,edge_ids,destinations,costs,capacities,types,nodes,edges};
 routecast::SearchWorkspace work{labels,known,settled,positions,frontier,scratch,left,right,node_capacity,frontier_capacity,path_capacity};
 auto termination=routecast::workspace_search(graph,source,targets,target_count,work_budget,work,counters);
 auto parent=[&](uint64_t r){return labels[r].parent;};auto edge=[&](uint64_t r){return labels[r].edge;};auto reached=[&](uint64_t r){return settled[r]!=0;};
 return uint8_t(routecast::commit_paths(termination,source,nodes,targets,target_count,parent,edge,reached,scratch,path_capacity,staged_edges,staged_capacity,staged_offsets,staged_offset_capacity,accepted_edges,accepted_capacity,accepted_offsets,accepted_offset_capacity,accepted_edge_count,accepted_target_count));
}
