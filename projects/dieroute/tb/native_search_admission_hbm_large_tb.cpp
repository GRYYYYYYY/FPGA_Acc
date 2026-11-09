#include "native_search_hbm_admission.hpp"
#include <array>
#include <cassert>
#include <cstring>
#include <tuple>
#include <iostream>
extern "C" void dieroute_native_search_admission_hbm(dieroute::NativeSearchLabelSlot*,dieroute::NativeSearchQueueEntry*,const dieroute::NativeSearchRelaxation*,std::uint32_t*,std::uint32_t*,std::uint32_t,std::uint32_t,std::uint32_t);
using namespace dieroute;
static auto key(const NativeSearchQueueEntry& e){return std::make_tuple(e.priority,e.cost,e.hops,e.node,e.parent);}
int main(){
 std::array<NativeSearchLabelSlot,1024> labels{};std::array<NativeSearchQueueEntry,1024> queue{};std::uint32_t count=0,status=99;unsigned calls=0;NativeSearchRelaxation r{};
 auto call=[&](unsigned credit){++calls;dieroute_native_search_admission_hbm(labels.data(),queue.data(),&r,&count,&status,1024,1024,credit);};
 auto reject=[&](NativeSearchAdmission expected,unsigned credit=1){auto old=labels;auto q=queue;auto c=count;call(credit);assert(status==std::uint32_t(expected)&&count==c);assert(std::memcmp(old.data(),labels.data(),sizeof(labels))==0&&std::memcmp(q.data(),queue.data(),sizeof(queue))==0);};
 for(unsigned epoch=1;epoch<=2;++epoch){
  count=0; // Explicit coordinator reset for the new search; not kernel-generated.
  for(unsigned i=0;i<1024;++i){
   r={epoch,0,2000-i,1999-i,i*1024,1,123,456};call(1);assert(status==0&&count==i+1);
   const auto& l=labels[i];assert(l.epoch==epoch&&l.node==i*1024&&l.cost==1999-i&&l.version==1&&l.hops==1&&l.parent==123&&l.edge==456&&l.flags==0);
   for(auto v:l.reserved)assert(v==0);
   for(unsigned j=1;j<count;++j)assert(key(queue[(j-1)/2])<=key(queue[j]));
  }
  r={epoch,0,9,8,1024*1024,1,123,456};reject(NativeSearchAdmission::label_capacity);
  r={epoch,0,9,8,0,1,123,456};reject(NativeSearchAdmission::stale);
  r.observed_version=1;reject(NativeSearchAdmission::queue_capacity);
 }
 r.epoch=1;reject(NativeSearchAdmission::invalid);
 r.epoch=2;r.reserved[0]=1;reject(NativeSearchAdmission::invalid);r.reserved[0]=0;
 reject(NativeSearchAdmission::invalid,2);
 std::cout<<"RTL_ADMISSION_EXPECTED_CALLS="<<calls<<" capacity=1024 epochs=2\n";
}
