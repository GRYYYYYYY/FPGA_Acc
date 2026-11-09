#include "native_search_hbm_frontier.hpp"
#include "native_search_hbm_admission.hpp"
#include <array>
#include <cassert>
#include <cstring>
using namespace dieroute;
extern "C" void dieroute_native_search_frontier_hbm(NativeSearchLabelSlot*,NativeSearchQueueEntry*,NativeSearchLabelSlot*,std::uint32_t*,std::uint32_t*,std::uint32_t,std::uint32_t,std::uint64_t);
int main(){
 std::array<NativeSearchLabelSlot,1024> labels{};std::array<NativeSearchQueueEntry,1024> queue{};std::uint32_t count=0;NativeSearchLabelSlot out{};
 auto invoke=[&](){std::uint32_t status=99;dieroute_native_search_frontier_hbm(labels.data(),queue.data(),&out,&count,&status,4,8,1);return NativeFrontierStatus(status);};
 NativeSearchRelaxation r{1,0,10,10,1,1,0,2};assert(native_search_admit<8>(labels.data(),4,queue.data(),8,count,r,true)==NativeSearchAdmission::accepted);
 r.observed_version=1;r.priority=r.cost=5;assert(native_search_admit<8>(labels.data(),4,queue.data(),8,count,r,true)==NativeSearchAdmission::accepted);
 assert(invoke()==NativeFrontierStatus::current);assert(out.cost==5&&out.version==3&&count==1);
 auto old=out;auto l=labels;assert(invoke()==NativeFrontierStatus::skipped);assert(count==0&&std::memcmp(&old,&out,sizeof(out))==0&&std::memcmp(l.data(),labels.data(),sizeof(labels))==0);
 assert(invoke()==NativeFrontierStatus::empty);
 labels[1].flags=0;labels[1].version=UINT64_MAX;queue[0]={5,5,1,1,0};count=1;auto q=queue;l=labels;
 assert(invoke()==NativeFrontierStatus::overflow);assert(count==1&&std::memcmp(q.data(),queue.data(),sizeof(queue))==0&&std::memcmp(l.data(),labels.data(),sizeof(labels))==0);
 queue[0].node=3;q=queue;assert(invoke()==NativeFrontierStatus::invalid);assert(count==1&&std::memcmp(q.data(),queue.data(),sizeof(queue))==0);
}
