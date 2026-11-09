#pragma once
#include "search_workspace.hpp"
#include "predecessor_path.hpp"
namespace routecast {
// Writes working reverse-edge sequence only. No accessor closures/objects.
inline PathStatus direct_reverse_path(uint64_t node,uint64_t root,uint64_t nodes,
 const SearchLabel* labels,uint64_t* reverse,uint64_t capacity,uint64_t& length){
 length=0;if(node>=nodes||root>=nodes)return PathStatus::invalid_parent;
 while(node!=root){
  if(length>=nodes)return PathStatus::invalid_parent;
  uint64_t p=labels[node].parent;if(p>=nodes)return PathStatus::invalid_parent;
  if(length==capacity)return PathStatus::capacity;
  reverse[length++]=labels[node].edge;node=p;
 }
 return PathStatus::ok;
}
// Comparison status must be checked before consuming the result. Buffers are
// disjoint working arrays. Ranks follow sorted raw node IDs.
inline int direct_label_compare(uint64_t a,uint64_t b,uint64_t root,uint64_t nodes,
 const SearchLabel* labels,uint64_t* left,uint64_t* right,uint64_t capacity,PathStatus& status){
 status=PathStatus::ok;
 if(a>=nodes||b>=nodes){status=PathStatus::invalid_parent;return 0;}
 if(labels[a].cost!=labels[b].cost)return labels[a].cost<labels[b].cost?-1:1;
 if(labels[a].hops!=labels[b].hops)return labels[a].hops<labels[b].hops?-1:1;
 uint64_t al=0,bl=0;status=direct_reverse_path(a,root,nodes,labels,left,capacity,al);if(status!=PathStatus::ok)return 0;
 status=direct_reverse_path(b,root,nodes,labels,right,capacity,bl);if(status!=PathStatus::ok)return 0;
 uint64_t limit=al<bl?al:bl;
 for(uint64_t i=0;i<limit;++i){uint64_t ae=left[al-1-i],be=right[bl-1-i];if(ae!=be)return ae<be?-1:1;}
 if(al!=bl)return al<bl?-1:1;
 return a<b?-1:(a>b?1:0);
}
}
