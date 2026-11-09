#include "native_search_hbm_queue.hpp"
#include <array>
#include <queue>
#include <random>
#include <cassert>
using namespace dieroute;
struct Greater {bool operator()(const NativeSearchQueueEntry&a,const NativeSearchQueueEntry&b)const{return native_search_queue_less(b,a);}};
static bool equal(const NativeSearchQueueEntry&a,const NativeSearchQueueEntry&b){return a.priority==b.priority&&a.cost==b.cost&&a.hops==b.hops&&a.node==b.node&&a.parent==b.parent;}
int main(){
 std::array<NativeSearchQueueEntry,127> storage{};std::uint32_t count=0;
 NativeSearchHBMQueue<127> heap(storage.data(),127,count);
 std::priority_queue<NativeSearchQueueEntry,std::vector<NativeSearchQueueEntry>,Greater> golden;
 std::mt19937 rng(456285);
 for(unsigned i=0;i<20000;++i){
  if((rng()%3)!=0){
   NativeSearchQueueEntry e{rng()%9,rng()%7,std::uint32_t(rng()%5),std::uint32_t(rng()%19),std::uint32_t(rng()%11)};auto before=storage;auto old=count;
   bool accepted=heap.push(e);assert(accepted==(golden.size()<storage.size()));
   if(accepted)golden.push(e);else {assert(count==old);for(unsigned j=0;j<storage.size();++j)assert(equal(storage[j],before[j]));}
  }else{
   NativeSearchQueueEntry e{99,98,97,96,95};auto old=e;
   bool accepted=heap.pop(e);assert(accepted==!golden.empty());
   if(accepted){assert(equal(e,golden.top()));golden.pop();}else assert(equal(e,old));
  }
  assert(count==golden.size());
 }
 while(!golden.empty()){NativeSearchQueueEntry e{};assert(heap.pop(e));assert(equal(e,golden.top()));golden.pop();}
 assert(count==0);
 std::uint32_t invalid=128;NativeSearchHBMQueue<127> bad(storage.data(),127,invalid);NativeSearchQueueEntry e{};assert(!bad.push(e)&&!bad.pop(e)&&invalid==128);
}
