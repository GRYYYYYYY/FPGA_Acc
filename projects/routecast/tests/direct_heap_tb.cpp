#ifdef NDEBUG
#undef NDEBUG
#endif
#include "direct_heap.hpp"
#include <array>
#include <cassert>
#include <random>
#include <set>
#include <tuple>
int main(){
 constexpr uint64_t N=32,C=7;std::array<uint64_t,N> positions;positions.fill(UINT64_MAX);std::array<uint64_t,C> heap{};uint64_t left[N],right[N],size=0;std::array<routecast::SearchLabel,N> labels;
 labels[0]={0,0,UINT64_MAX,UINT64_MAX};for(uint64_t i=1;i<N;++i)labels[i]={0,1,0,i%5};std::set<std::tuple<uint64_t,uint64_t,uint64_t>> oracle;std::mt19937 rng(731);
 for(unsigned step=0;step<10000;++step){uint64_t node=1+rng()%(N-1);
  if(rng()%3){bool existing=positions[node]!=UINT64_MAX;auto oldheap=heap;auto oldpos=positions;uint64_t oldsize=size;
   if(existing){oracle.erase({labels[node].cost.low,labels[node].edge,node});labels[node].cost=labels[node].cost.low/2;}else labels[node].cost=rng()%20;
   auto status=routecast::direct_heap_insert(node,heap.data(),positions.data(),size,C,N,0,labels.data(),left,right,N);
   if(!existing&&oracle.size()==C){assert(status==routecast::DirectHeapStatus::capacity);assert(oldheap==heap&&oldpos==positions&&oldsize==size);}else{assert(status==routecast::DirectHeapStatus::ok);oracle.insert({labels[node].cost.low,labels[node].edge,node});}
  }else{uint64_t result=999;auto status=routecast::direct_heap_pop(result,heap.data(),positions.data(),size,N,0,labels.data(),left,right,N);if(oracle.empty())assert(status==routecast::DirectHeapStatus::empty);else{assert(status==routecast::DirectHeapStatus::ok);assert(result==std::get<2>(*oracle.begin()));oracle.erase(oracle.begin());}}
  assert(size==oracle.size());for(uint64_t i=0;i<size;++i){assert(positions[heap[i]]==i);if(i){routecast::PathStatus status;assert(routecast::direct_label_compare(heap[i],heap[(i-1)/2],0,N,labels.data(),left,right,N,status)>=0);assert(status==routecast::PathStatus::ok);}}
 }
 positions.fill(UINT64_MAX);size=0;labels[1].cost=0;labels[2].cost=0;
 assert(routecast::direct_heap_insert(1,heap.data(),positions.data(),size,C,N,0,labels.data(),left,right,0)==routecast::DirectHeapStatus::ok);
 assert(routecast::direct_heap_insert(2,heap.data(),positions.data(),size,C,N,0,labels.data(),left,right,0)==routecast::DirectHeapStatus::path_capacity);
}
