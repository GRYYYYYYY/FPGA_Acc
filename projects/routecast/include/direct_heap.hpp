#pragma once
#include "direct_path.hpp"
namespace routecast {
enum class DirectHeapStatus { ok, empty, invalid_rank, capacity, path_capacity, invalid_parent };
inline DirectHeapStatus direct_heap_path_status(PathStatus s){return s==PathStatus::capacity?DirectHeapStatus::path_capacity:DirectHeapStatus::invalid_parent;}
inline void direct_heap_swap(uint64_t* heap,uint64_t* positions,uint64_t a,uint64_t b){uint64_t t=heap[a];heap[a]=heap[b];heap[b]=t;positions[heap[a]]=a;positions[heap[b]]=b;}
// positions initialized to UINT64_MAX; labels for existing entries only decrease.
// Capacity/invalid-rank rejection leaves heap storage unchanged. Path failure may
// change working heap state; caller must abort query and retain accepted output.
inline DirectHeapStatus direct_heap_insert(uint64_t node,uint64_t* heap,uint64_t* positions,
 uint64_t& size,uint64_t capacity,uint64_t nodes,uint64_t root,const SearchLabel* labels,
 uint64_t* left,uint64_t* right,uint64_t path_capacity){
 if(node>=nodes)return DirectHeapStatus::invalid_rank;
 uint64_t i=positions[node];
 if(i==UINT64_MAX){if(size==capacity)return DirectHeapStatus::capacity;i=size++;heap[i]=node;positions[node]=i;}
 while(i){uint64_t p=(i-1)/2;PathStatus status;int c=direct_label_compare(heap[i],heap[p],root,nodes,labels,left,right,path_capacity,status);if(status!=PathStatus::ok)return direct_heap_path_status(status);if(c>=0)break;direct_heap_swap(heap,positions,i,p);i=p;}
 return DirectHeapStatus::ok;
}
inline DirectHeapStatus direct_heap_pop(uint64_t& node,uint64_t* heap,uint64_t* positions,
 uint64_t& size,uint64_t nodes,uint64_t root,const SearchLabel* labels,
 uint64_t* left,uint64_t* right,uint64_t path_capacity){
 if(!size)return DirectHeapStatus::empty;
 node=heap[0];positions[node]=UINT64_MAX;--size;
 if(size){heap[0]=heap[size];positions[heap[0]]=0;uint64_t i=0;
  while(i<size/2){uint64_t child=2*i+1;PathStatus status;
   if(child+1<size){int c=direct_label_compare(heap[child+1],heap[child],root,nodes,labels,left,right,path_capacity,status);if(status!=PathStatus::ok)return direct_heap_path_status(status);if(c<0)++child;}
   int c=direct_label_compare(heap[child],heap[i],root,nodes,labels,left,right,path_capacity,status);if(status!=PathStatus::ok)return direct_heap_path_status(status);if(c>=0)break;direct_heap_swap(heap,positions,i,child);i=child;
  }
 }
 return DirectHeapStatus::ok;
}
}
