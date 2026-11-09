#include "native_search_hbm_frontier.hpp"
#include "native_search_hbm_admission.hpp"
#include <array>
#include <cassert>
#include <cstring>
using namespace dieroute;
int main(){
 std::array<NativeSearchLabelSlot,4> labels{};std::array<NativeSearchQueueEntry,8> queue{};std::uint32_t count=0;NativeSearchLabelSlot out{};
 NativeSearchRelaxation r{1,0,10,10,1,1,0,2};assert(native_search_admit<8>(labels.data(),4,queue.data(),8,count,r,true)==NativeSearchAdmission::accepted);
 r.observed_version=1;r.priority=r.cost=5;assert(native_search_admit<8>(labels.data(),4,queue.data(),8,count,r,true)==NativeSearchAdmission::accepted);
 assert(native_search_take_frontier<8>(labels.data(),4,queue.data(),8,count,1,out)==NativeFrontierStatus::current);assert(out.cost==5&&out.version==3&&count==1);
 auto old=out;auto l=labels;assert(native_search_take_frontier<8>(labels.data(),4,queue.data(),8,count,1,out)==NativeFrontierStatus::skipped);assert(count==0&&std::memcmp(&old,&out,sizeof(out))==0&&std::memcmp(l.data(),labels.data(),sizeof(labels))==0);
 assert(native_search_take_frontier<8>(labels.data(),4,queue.data(),8,count,1,out)==NativeFrontierStatus::empty);
 labels[1].flags=0;labels[1].version=UINT64_MAX;queue[0]={5,5,1,1,0};count=1;auto q=queue;l=labels;
 assert(native_search_take_frontier<8>(labels.data(),4,queue.data(),8,count,1,out)==NativeFrontierStatus::overflow);assert(count==1&&std::memcmp(q.data(),queue.data(),sizeof(queue))==0&&std::memcmp(l.data(),labels.data(),sizeof(labels))==0);
 queue[0].node=3;q=queue;assert(native_search_take_frontier<8>(labels.data(),4,queue.data(),8,count,1,out)==NativeFrontierStatus::invalid);assert(count==1&&std::memcmp(q.data(),queue.data(),sizeof(queue))==0);
}
