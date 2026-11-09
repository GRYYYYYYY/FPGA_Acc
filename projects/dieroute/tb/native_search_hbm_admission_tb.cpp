#include "native_search_hbm_admission.hpp"
#include <array>
#include <cassert>
#include <cstring>
using namespace dieroute;
int main(){
 std::array<NativeSearchLabelSlot,4> labels{};std::array<NativeSearchQueueEntry,4> queue{};std::uint32_t count=0;
 NativeSearchRelaxation r{1,0,8,7,0,1,1,2};
 auto reject=[&](NativeSearchAdmission expected,bool credit=true){auto l=labels;auto q=queue;auto c=count;assert(native_search_admit<4>(labels.data(),4,queue.data(),4,count,r,credit)==expected);assert(count==c&&std::memcmp(l.data(),labels.data(),sizeof(labels))==0&&std::memcmp(q.data(),queue.data(),sizeof(queue))==0);};
 reject(NativeSearchAdmission::label_capacity,false);
 assert(native_search_admit<4>(labels.data(),4,queue.data(),4,count,r,true)==NativeSearchAdmission::accepted);assert(count==1&&labels[0].version==1);
 reject(NativeSearchAdmission::stale);r.observed_version=1;reject(NativeSearchAdmission::dominated);
 r.cost=6;r.priority=7;assert(native_search_admit<4>(labels.data(),4,queue.data(),4,count,r,false)==NativeSearchAdmission::accepted);assert(labels[0].version==2&&count==2);
 r.observed_version=2;labels[0].flags=1;reject(NativeSearchAdmission::protected_label);labels[0].flags=0;
 r.node=4;r.observed_version=0;r.cost=5;assert(native_search_admit<4>(labels.data(),4,queue.data(),4,count,r,true)==NativeSearchAdmission::accepted);assert(labels[1].node==4);
 r.node=8;assert(native_search_admit<4>(labels.data(),4,queue.data(),4,count,r,true)==NativeSearchAdmission::accepted);
 r.node=12;reject(NativeSearchAdmission::queue_capacity);assert(labels[3].epoch==0);
 count=0;r.node=0;r.observed_version=2;r.cost=4;labels[0].version=UINT64_MAX;r.observed_version=UINT64_MAX;reject(NativeSearchAdmission::overflow);
 r.cost=UINT64_MAX;reject(NativeSearchAdmission::invalid);
}
