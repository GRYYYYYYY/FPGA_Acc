#include "native_search_hbm_relax_observed.hpp"
#include "sparse_label_worker.hpp"
#include <array>
#include <cassert>
#include <random>
#include <tuple>
using namespace dieroute;
int main(){
 std::mt19937_64 rng(431927);
 for(unsigned trial=0;trial<10000;++trial){
  std::array<NativeSearchLabelSlot,8> labels{};
  std::array<NativeSearchQueueEntry,8> queue{};
  std::array<NativeSearchResourceObservation,8> journal{};
  std::uint32_t queued=0,used=0;
  SparseLabelWorker reference;reference.reset(0,1,8);
  auto parent_cost=rng()%100;auto depth=std::uint32_t(rng()%8);
  reference.seed(0,parent_cost,parent_cost,depth,true);reference.pop();reference.close(0);
  NativeSearchLabelSlot parent{1,parent_cost,2,0,depth,UINT32_MAX,UINT32_MAX,3};
  if(rng()%2){
   auto req=LabelPacket::message(1,1,1,LabelOp::relax,0,0);
   auto cost=rng()%200;auto hops=std::uint32_t(1+rng()%10);
   req.value(cost,cost,hops,0,17,0,0);
   assert(reference.receive(req,[](std::uint32_t){return 0U;},true).status()==LabelStatus::accepted);
   reference.pop();labels[1]={1,cost,1,1,hops,0,17,0};
   if(rng()%5==0){reference.close(1);labels[1].flags=1;++labels[1].version;}
  }
  auto old=reference.local(1);
  NativeSearchResourceObservation observation{1,rng(),rng()%20,rng()%50,7,1,0,0};
  bool own=rng()%2,credit=rng()%2;auto present=rng()%20;
  auto potential=rng()%10==0?UINT64_MAX:rng()%30;auto bound=rng()%250;
  auto expected=NativeObservedRelaxStatus::protected_label;
  bool read=!old.closed&&!old.root;
  if(read){
   auto delta=1+observation.history+present*(observation.occupancy-(own&&observation.occupancy?1:0));
   auto cost=parent_cost+delta;auto hops=depth+1;std::uint32_t p=0,edge=13;
   if(std::tie(cost,hops,p,edge)>=std::tie(old.cost,old.hops,old.parent,old.edge))expected=NativeObservedRelaxStatus::dominated;
   else if(potential==UINT64_MAX)expected=NativeObservedRelaxStatus::unreachable;
   else if(cost+potential>bound)expected=NativeObservedRelaxStatus::cost_limited;
   else{
    auto req=LabelPacket::message(1,2,1,LabelOp::relax,0,0);req.value(cost,cost+potential,hops,0,13,0,old.version);
    auto reply=reference.receive(req,[](std::uint32_t){return 0U;},credit);
    assert(reply.status()==LabelStatus::accepted||reply.status()==LabelStatus::budget);
    expected=reply.status()==LabelStatus::accepted?NativeObservedRelaxStatus::accepted:NativeObservedRelaxStatus::label_capacity;
   }
  }
  auto got=native_search_relax_observed<8>(labels.data(),8,queue.data(),8,queued,parent,1,13,observation,7,journal.data(),8,used,own,present,potential,bound,credit);
  assert(got==expected&&used==unsigned(read));
  if(read)assert(journal[0].version==observation.version&&journal[0].occupancy==observation.occupancy&&journal[0].history==observation.history);
  auto target=reference.local(1);auto actual=labels[1];
  assert(std::tie(actual.cost,actual.hops,actual.parent,actual.edge,actual.version)==std::tie(target.cost,target.hops,target.parent,target.edge,target.version));
  assert(queued==unsigned(expected==NativeObservedRelaxStatus::accepted));
  if(queued){auto e=reference.pop();assert(e==std::make_tuple(queue[0].priority,queue[0].cost,queue[0].hops,queue[0].node,queue[0].parent));}
 }
}
