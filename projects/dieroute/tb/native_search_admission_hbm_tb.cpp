#include "native_search_hbm_admission.hpp"
#include <array>
#include <cassert>
#include <cstring>
using namespace dieroute;
extern "C" void dieroute_native_search_admission_hbm(NativeSearchLabelSlot*,NativeSearchQueueEntry*,const NativeSearchRelaxation*,std::uint32_t*,std::uint32_t*,std::uint32_t,std::uint32_t,std::uint32_t);
int main(){
 std::array<NativeSearchLabelSlot,1024> labels{};std::array<NativeSearchQueueEntry,1024> queue{};std::uint32_t count=0;
 NativeSearchRelaxation r{1,0,8,7,0,1,1,2};
 auto invoke=[&](bool credit){std::uint32_t status=99;dieroute_native_search_admission_hbm(labels.data(),queue.data(),&r,&count,&status,4,4,credit?1:0);return NativeSearchAdmission(status);};
 auto reject=[&](NativeSearchAdmission expected,bool credit=true){auto l=labels;auto q=queue;auto c=count;assert(invoke(credit)==expected);assert(count==c&&std::memcmp(l.data(),labels.data(),sizeof(labels))==0&&std::memcmp(q.data(),queue.data(),sizeof(queue))==0);};
 reject(NativeSearchAdmission::label_capacity,false);
 assert(invoke(true)==NativeSearchAdmission::accepted);assert(count==1&&labels[0].version==1);
 reject(NativeSearchAdmission::stale);r.observed_version=1;reject(NativeSearchAdmission::dominated);
 r.cost=6;r.priority=7;assert(invoke(false)==NativeSearchAdmission::accepted);assert(labels[0].version==2&&count==2);
 r.observed_version=2;labels[0].flags=1;reject(NativeSearchAdmission::protected_label);labels[0].flags=0;
 r.node=4;r.observed_version=0;r.cost=5;assert(invoke(true)==NativeSearchAdmission::accepted);assert(labels[1].node==4);
 r.node=8;assert(invoke(true)==NativeSearchAdmission::accepted);
 r.node=12;reject(NativeSearchAdmission::queue_capacity);assert(labels[3].epoch==0);
 count=0;r.node=0;r.observed_version=2;r.cost=4;labels[0].version=UINT64_MAX;r.observed_version=UINT64_MAX;reject(NativeSearchAdmission::overflow);
 r.cost=UINT64_MAX;reject(NativeSearchAdmission::invalid);
}
