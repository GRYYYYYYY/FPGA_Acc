#pragma once
#include <cstdint>
namespace routecast {
enum class PathStatus { ok, invalid_parent, capacity };
// Scratch/output must be disjoint valid caller-owned regions.
// Scratch is caller-owned working memory. Accepted output and length are only
// modified after full reconstruction succeeds. parent/edge accessors are pure.
template<class Parent,class Edge>
PathStatus reconstruct_path(uint64_t node,uint64_t root,uint64_t nodes,
 Parent parent,Edge edge,uint64_t* scratch,uint64_t scratch_capacity,
 uint64_t* output,uint64_t output_capacity,uint64_t& output_length){
 if(node>=nodes||root>=nodes)return PathStatus::invalid_parent;
 uint64_t length=0;
 while(node!=root){
  if(length>=nodes)return PathStatus::invalid_parent;
  uint64_t p=parent(node);
  if(p>=nodes)return PathStatus::invalid_parent;
  if(length==scratch_capacity)return PathStatus::capacity;
  scratch[length++]=edge(node);node=p;
 }
 if(length>output_capacity)return PathStatus::capacity;
 for(uint64_t i=0;i<length;++i)output[i]=scratch[length-1-i];
 output_length=length;return PathStatus::ok;
}
}
