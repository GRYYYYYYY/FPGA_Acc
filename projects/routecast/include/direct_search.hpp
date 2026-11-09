#pragma once
#include "workspace_search.hpp"
#include "direct_heap.hpp"
namespace routecast {
inline SearchTermination direct_search(const uint64_t* rows,const uint64_t* edge_ids,const uint64_t* destinations,const uint64_t* costs,const uint64_t* capacities,const uint8_t* types,uint64_t nodes,uint64_t edges,uint64_t source,const uint64_t* targets,uint64_t count,uint64_t work_budget,SearchLabel* labels,uint8_t* known,uint8_t* settled,uint64_t* positions,uint64_t* frontier,uint64_t* left,uint64_t* right,uint64_t node_capacity,uint64_t frontier_capacity,uint64_t path_capacity,SearchCounters& counters){
 counters={};
 if(!nodes||source>=nodes)return SearchTermination::invalid_input;
// Host null pointers are invalid; AXI base address zero is a valid device offset.
#ifndef __SYNTHESIS__
 if(!rows||!types||!capacities||(count&&!targets)||(edges&&(!edge_ids||!destinations||!costs)))return SearchTermination::invalid_input;
#endif
 if(types[source]!=0)return SearchTermination::invalid_input;
 for(uint64_t i=0;i<count;++i)if(targets[i]>=nodes||types[targets[i]]!=1)return SearchTermination::invalid_input;
 if(rows[0]!=0||rows[nodes]!=edges)return SearchTermination::invalid_input;
 for(uint64_t i=0;i<nodes;++i)if(rows[i]>rows[i+1])return SearchTermination::invalid_input;
 for(uint64_t i=0;i<edges;++i)if(destinations[i]>=nodes||edge_ids[i]>=edges)return SearchTermination::invalid_input;
 if(nodes>node_capacity)return SearchTermination::invalid_input;
#ifndef __SYNTHESIS__
 if(!labels||!known||!settled||!positions||(frontier_capacity&&!frontier)||(path_capacity&&(!left||!right)))return SearchTermination::invalid_input;
#endif
 for(uint64_t i=0;i<nodes;++i){labels[i]={0,0,UINT64_MAX,UINT64_MAX};known[i]=0;settled[i]=0;positions[i]=UINT64_MAX;}
 if(!count)return SearchTermination::targets_complete;
 if(!capacities[source])return SearchTermination::frontier_empty;
 uint64_t heap_size=0;known[source]=1;
 auto initial=direct_heap_insert(source,frontier,positions,heap_size,frontier_capacity,nodes,source,labels,left,right,path_capacity);
 if(initial!=DirectHeapStatus::ok)return initial==DirectHeapStatus::capacity?SearchTermination::frontier_capacity:initial==DirectHeapStatus::path_capacity?SearchTermination::path_capacity:SearchTermination::invalid_input;
 uint64_t remain=count;
 while(heap_size){
  if(heap_size>counters.peak_frontier)counters.peak_frontier=heap_size;
  if(counters.settled==work_budget)return SearchTermination::work_budget;
  uint64_t node;auto pop_status=direct_heap_pop(node,frontier,positions,heap_size,nodes,source,labels,left,right,path_capacity);if(pop_status!=DirectHeapStatus::ok)return pop_status==DirectHeapStatus::path_capacity?SearchTermination::path_capacity:SearchTermination::invalid_input;
  settled[node]=1;++counters.settled;
  for(uint64_t i=0;i<count;++i)if(targets[i]==node)--remain;
  if(!remain)return SearchTermination::targets_complete;
  for(uint64_t slot=rows[node];slot<rows[node+1];++slot){
   ++counters.edge_visits;uint64_t d=destinations[slot],weight=costs[slot];
   if(settled[d]||weight==UINT64_MAX)continue;
   SearchLabel candidate{labels[node].cost+weight,labels[node].hops+1,node,edge_ids[slot]};auto old=labels[d];
   bool better=!known[d]||candidate.cost<old.cost||(candidate.cost==old.cost&&candidate.hops<old.hops);
   if(known[d]&&candidate.cost==old.cost&&candidate.hops==old.hops){
    uint64_t al=0,bl=0;auto status=direct_reverse_path(node,source,nodes,labels,left,path_capacity,al);if(status!=PathStatus::ok)return status==PathStatus::capacity?SearchTermination::path_capacity:SearchTermination::invalid_input;
    status=direct_reverse_path(d,source,nodes,labels,right,path_capacity,bl);if(status!=PathStatus::ok)return status==PathStatus::capacity?SearchTermination::path_capacity:SearchTermination::invalid_input;
    if(al>=path_capacity)return SearchTermination::path_capacity;
    // Compare forward candidate(parentpath + edge) against reverse oldpath.
    uint64_t candidate_length=al+1,limit=candidate_length<bl?candidate_length:bl;bool equal=true;better=false;
    for(uint64_t i=0;i<limit;++i){uint64_t ae=i==al?candidate.edge:left[al-1-i],be=right[bl-1-i];if(ae!=be){better=ae<be;equal=false;break;}}
    if(equal)better=candidate_length<bl;
   }
   if(better){labels[d]=candidate;known[d]=1;auto status=direct_heap_insert(d,frontier,positions,heap_size,frontier_capacity,nodes,source,labels,left,right,path_capacity);if(status!=DirectHeapStatus::ok)return status==DirectHeapStatus::capacity?SearchTermination::frontier_capacity:status==DirectHeapStatus::path_capacity?SearchTermination::path_capacity:SearchTermination::invalid_input;}
  }
 }
 return SearchTermination::frontier_empty;
}
}
