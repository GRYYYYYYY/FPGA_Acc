#include "native_search_hbm_label_ops.hpp"
#include <array>
#include <cassert>
#include <cstring>
using namespace dieroute;
extern "C" void dieroute_native_search_label_ops_hbm(NativeSearchLabelSlot*,const NativeSearchQueueEntry*,NativeSearchLabelSlot*,std::uint32_t*,std::uint32_t,std::uint64_t,std::uint32_t);
int main(){
 std::array<NativeSearchLabelSlot,1024> labels{};labels[1]={3,10,7,1,2,0,9,2};NativeSearchLabelSlot output{};NativeSearchQueueEntry entry{10,9,2,1,0};
 auto invoke=[&](unsigned op,std::uint64_t epoch,unsigned node){auto command=entry;command.node=node;std::uint32_t status=99;dieroute_native_search_label_ops_hbm(labels.data(),&command,&output,&status,4,epoch,op);return NativeSearchLabelOpStatus(status);};
 auto reject=[&](NativeSearchLabelOpStatus status){auto before=labels;auto old=output;assert(invoke(2,3,entry.node)==status);assert(std::memcmp(before.data(),labels.data(),sizeof(labels))==0&&std::memcmp(&old,&output,sizeof(output))==0);};
 reject(NativeSearchLabelOpStatus::stale);entry.cost=10;entry.hops=1;reject(NativeSearchLabelOpStatus::stale);
 entry.hops=2;entry.parent=123;assert(invoke(2,3,entry.node)==NativeSearchLabelOpStatus::ok);assert(output.version==8&&output.flags==3&&output.parent==0);
 reject(NativeSearchLabelOpStatus::closed);entry.node=2;reject(NativeSearchLabelOpStatus::missing);
 auto old=output;assert(invoke(1,3,2)==NativeSearchLabelOpStatus::missing);assert(std::memcmp(&old,&output,sizeof(output))==0);
 assert(invoke(1,3,1)==NativeSearchLabelOpStatus::ok&&output.edge==9);
 assert(invoke(1,2,1)==NativeSearchLabelOpStatus::invalid);
 labels[1].flags=0;labels[1].version=UINT64_MAX;entry.node=1;reject(NativeSearchLabelOpStatus::overflow);
}
