#ifdef NDEBUG
#undef NDEBUG
#endif
#include "indexed_heap.hpp"
#include <array>
#include <cassert>
#include <random>
#include <set>
#include <utility>
int main(){
 constexpr uint64_t N=31,C=7;
 std::array<uint64_t,N> positions{},cost{};std::array<uint64_t,C> slots{};
 auto less=[&](uint64_t a,uint64_t b){return std::make_pair(cost[a],a)<std::make_pair(cost[b],b);};
 routecast::IndexedHeap<decltype(less)> heap(slots.data(),positions.data(),N,C,less);
 std::set<std::pair<uint64_t,uint64_t>> oracle;std::mt19937 rng(731);
 for(unsigned step=0;step<10000;++step){
  uint64_t node=rng()%N;
  if(rng()%3){
   auto oldslots=slots;auto oldpos=positions;auto oldsize=heap.size;
   bool existing=positions[node]!=routecast::no_position;
   if(existing){oracle.erase({cost[node],node});cost[node]/=2;}else cost[node]=rng()%100;
   auto result=heap.decrease_or_insert(node);
   if(!existing&&oracle.size()==C){assert(result==routecast::HeapStatus::capacity);assert(slots==oldslots&&positions==oldpos&&heap.size==oldsize);}
   else{assert(result==routecast::HeapStatus::ok);oracle.insert({cost[node],node});}
  }else{
   uint64_t got=999;bool ok=heap.pop(got);assert(ok==!oracle.empty());if(ok){assert(got==oracle.begin()->second);oracle.erase(oracle.begin());}
  }
  assert(heap.size==oracle.size());
  for(uint64_t i=0;i<heap.size;++i){assert(positions[slots[i]]==i);if(i)assert(!less(slots[i],slots[(i-1)/2]));}
 }
 auto oldslots=slots;auto oldpos=positions;assert(heap.decrease_or_insert(N)==routecast::HeapStatus::invalid_rank);assert(slots==oldslots&&positions==oldpos);
 uint64_t zero_slots[1],zero_pos[1];auto always=[](uint64_t,uint64_t){return false;};routecast::IndexedHeap<decltype(always)> zero(zero_slots,zero_pos,1,0,always);assert(zero.decrease_or_insert(0)==routecast::HeapStatus::capacity);uint64_t node;assert(!zero.pop(node));
}
