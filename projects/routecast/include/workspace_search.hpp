#pragma once
#include "search_workspace.hpp"
#include "indexed_heap.hpp"
#include "path_transaction.hpp"
namespace routecast {
struct PreparedSearchGraph {
 const uint64_t *rows,*edge_ids,*destinations,*costs,*capacities;
 const uint8_t* types;uint64_t nodes,edges;
};
struct SearchCounters {uint64_t settled=0,edge_visits=0,peak_frontier=0;};
// Graph is authenticated by host and ranks follow increasing raw IDs. No
// allocation or accepted-output writes; commit_paths consumes this termination.
inline SearchTermination workspace_search(const PreparedSearchGraph& g,
 uint64_t source,const uint64_t* targets,uint64_t count,uint64_t work_budget,
 SearchWorkspace& w,SearchCounters& counters){
 counters={};
 if(!g.nodes||source>=g.nodes||!g.rows||!g.types||!g.capacities||(count&&!targets)||(g.edges&&(!g.edge_ids||!g.destinations||!g.costs)))return SearchTermination::invalid_input;
 if(g.types[source]!=0)return SearchTermination::invalid_input;
 for(uint64_t i=0;i<count;++i)if(targets[i]>=g.nodes||g.types[targets[i]]!=1)return SearchTermination::invalid_input;
 if(g.rows[0]!=0||g.rows[g.nodes]!=g.edges)return SearchTermination::invalid_input;
 for(uint64_t i=0;i<g.nodes;++i)if(g.rows[i]>g.rows[i+1])return SearchTermination::invalid_input;
 for(uint64_t i=0;i<g.edges;++i)if(g.destinations[i]>=g.nodes||g.edge_ids[i]>=g.edges)return SearchTermination::invalid_input;
 if(initialize_workspace(w,g.nodes)!=WorkspaceStatus::ok)return SearchTermination::invalid_input;
 if(!count)return SearchTermination::targets_complete;
 if(!g.capacities[source])return SearchTermination::frontier_empty;
 SearchTermination failure=SearchTermination::targets_complete;
 auto path=[&](uint64_t n,uint64_t* output){uint64_t length=0;auto parent=[&](uint64_t r){return w.labels[r].parent;};auto edge=[&](uint64_t r){return w.labels[r].edge;};auto status=reconstruct_path(n,source,g.nodes,parent,edge,w.scratch,w.path_capacity,output,w.path_capacity,length);if(status!=PathStatus::ok)failure=status==PathStatus::capacity?SearchTermination::path_capacity:SearchTermination::invalid_input;return length;};
 auto lex=[](const uint64_t*a,uint64_t al,const uint64_t*b,uint64_t bl){uint64_t lim=al<bl?al:bl;for(uint64_t i=0;i<lim;++i)if(a[i]!=b[i])return a[i]<b[i];return al<bl;};
 auto less=[&](uint64_t a,uint64_t b){auto& la=w.labels[a];auto& lb=w.labels[b];if(la.cost!=lb.cost)return la.cost<lb.cost;if(la.hops!=lb.hops)return la.hops<lb.hops;uint64_t al=path(a,w.left),bl=path(b,w.right);if(failure!=SearchTermination::targets_complete)return a<b;if(lex(w.left,al,w.right,bl))return true;if(lex(w.right,bl,w.left,al))return false;return a<b;};
 IndexedHeap<decltype(less)> heap(w.frontier,w.positions,g.nodes,w.frontier_capacity,less);
 w.known[source]=1;
 if(heap.decrease_or_insert(source)!=HeapStatus::ok)return SearchTermination::frontier_capacity;
 uint64_t remain=count;
 while(heap.size){
  if(heap.size>counters.peak_frontier)counters.peak_frontier=heap.size;
  if(counters.settled==work_budget)return SearchTermination::work_budget;
  uint64_t node;heap.pop(node);if(failure!=SearchTermination::targets_complete)return failure;
  w.settled[node]=1;++counters.settled;
  for(uint64_t i=0;i<count;++i)if(targets[i]==node)--remain;
  if(!remain)return SearchTermination::targets_complete;
  for(uint64_t slot=g.rows[node];slot<g.rows[node+1];++slot){
   ++counters.edge_visits;uint64_t d=g.destinations[slot],weight=g.costs[slot];
   if(w.settled[d]||weight==UINT64_MAX)continue;
   SearchLabel candidate{w.labels[node].cost+weight,w.labels[node].hops+1,node,g.edge_ids[slot]};auto old=w.labels[d];
   bool better=!w.known[d]||candidate.cost<old.cost||(candidate.cost==old.cost&&candidate.hops<old.hops);
   if(w.known[d]&&candidate.cost==old.cost&&candidate.hops==old.hops){uint64_t al=path(node,w.left),bl=path(d,w.right);if(failure!=SearchTermination::targets_complete)return failure;if(al>=w.path_capacity)return SearchTermination::path_capacity;w.left[al++]=candidate.edge;better=lex(w.left,al,w.right,bl);}
   if(better){w.labels[d]=candidate;w.known[d]=1;if(heap.decrease_or_insert(d)!=HeapStatus::ok)return SearchTermination::frontier_capacity;if(failure!=SearchTermination::targets_complete)return failure;}
  }
 }
 return SearchTermination::frontier_empty;
}
}
