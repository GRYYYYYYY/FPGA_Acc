#include "native_search_hbm_relax_observed.hpp"
#include <array>
#include <cassert>
#include <cstring>
using namespace dieroute;
int main(){
 std::array<NativeSearchLabelSlot,8> labels{};
 std::array<NativeSearchQueueEntry,8> queue{};
 std::array<NativeSearchResourceObservation,8> journal{};
 std::uint32_t queued=0,used=0;
 NativeSearchLabelSlot parent{1,5,1,0,2,UINT32_MAX,UINT32_MAX,3};
 NativeSearchResourceObservation value{1,9,2,4,7,1,0,0};
 auto call=[&](std::uint64_t potential=0,std::uint64_t bound=UINT64_MAX){return native_search_relax_observed<8>(labels.data(),8,queue.data(),8,queued,parent,1,13,value,7,journal.data(),8,used,true,10,potential,bound,true);};
 assert(call()==NativeObservedRelaxStatus::accepted&&used==1&&queued==1);
 assert(labels[1].cost==20&&labels[1].hops==3&&labels[1].edge==13);
 auto before=labels;auto q=queue;
 assert(call()==NativeObservedRelaxStatus::dominated&&used==2&&queued==1);
 assert(std::memcmp(before.data(),labels.data(),sizeof(labels))==0&&std::memcmp(q.data(),queue.data(),sizeof(queue))==0);
 labels[1].flags=1;assert(call()==NativeObservedRelaxStatus::protected_label&&used==2);
 labels[1]=NativeSearchLabelSlot{};
 assert(call(UINT64_MAX)==NativeObservedRelaxStatus::unreachable&&used==3&&queued==1);
 assert(call(0,19)==NativeObservedRelaxStatus::cost_limited&&used==4&&queued==1);
 value.history=UINT64_MAX;assert(call()==NativeObservedRelaxStatus::cost_overflow&&used==5&&journal[4].history==UINT64_MAX);
 value.history=4;value.session=8;assert(call()==NativeObservedRelaxStatus::invalid&&used==5);
 value.session=7;used=8;assert(call()==NativeObservedRelaxStatus::journal_full&&used==8);
}
