#include "native_search_hbm_label_ops.hpp"
#include <array>
#include <cassert>
#include <cstring>
using namespace dieroute;
int main(){
 std::array<NativeSearchLabelSlot,4> labels{};labels[1]={3,10,7,1,2,0,9,2};NativeSearchLabelSlot output{};NativeSearchQueueEntry entry{10,9,2,1,0};
 auto reject=[&](NativeSearchLabelOpStatus status){auto before=labels;auto old=output;assert(native_search_label_close<4>(labels.data(),4,3,entry,output)==status);assert(std::memcmp(before.data(),labels.data(),sizeof(labels))==0&&std::memcmp(&old,&output,sizeof(output))==0);};
 reject(NativeSearchLabelOpStatus::stale);entry.cost=10;entry.hops=1;reject(NativeSearchLabelOpStatus::stale);
 entry.hops=2;entry.parent=123;assert(native_search_label_close<4>(labels.data(),4,3,entry,output)==NativeSearchLabelOpStatus::ok);assert(output.version==8&&output.flags==3&&output.parent==0);
 reject(NativeSearchLabelOpStatus::closed);entry.node=2;reject(NativeSearchLabelOpStatus::missing);
 auto old=output;assert(native_search_label_read<4>(labels.data(),4,3,2,output)==NativeSearchLabelOpStatus::missing);assert(std::memcmp(&old,&output,sizeof(output))==0);
 assert(native_search_label_read<4>(labels.data(),4,3,1,output)==NativeSearchLabelOpStatus::ok&&output.edge==9);
 assert(native_search_label_read<4>(labels.data(),4,2,1,output)==NativeSearchLabelOpStatus::invalid);
 labels[1].flags=0;labels[1].version=UINT64_MAX;entry.node=1;reject(NativeSearchLabelOpStatus::overflow);
}
