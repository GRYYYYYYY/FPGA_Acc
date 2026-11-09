#include "native_search_hbm_relax_observed.hpp"
#include "native_search_hbm_frontier.hpp"
#include "native_search_hbm_seed.hpp"
#include <array>
#include <cassert>
#include <cstring>
using namespace dieroute;
extern "C" void dieroute_native_search_worker_hbm(NativeSearchLabelSlot* labels,NativeSearchQueueEntry* queue,NativeSearchResourceObservation* journal,const NativeSearchLabelSlot* parent,const std::uint64_t* observation_words,std::uint64_t* metadata,std::uint32_t label_capacity,std::uint32_t queue_capacity,std::uint32_t journal_capacity,std::uint32_t dst,std::uint32_t edge,std::uint64_t session,std::uint32_t own,std::uint64_t present,std::uint64_t potential,std::uint64_t max_cost,std::uint32_t credit,NativeSearchLabelSlot* frontier_output,std::uint32_t operation);
int main(){
 std::array<NativeSearchLabelSlot,1024> labels{};
 std::array<NativeSearchQueueEntry,1024> queue{};
 std::array<NativeSearchResourceObservation,1024> journal{};
 std::uint32_t queued=0,used=0;
 NativeSearchLabelSlot frontier_output{};
 NativeSearchLabelSlot parent{1,5,1,0,2,UINT32_MAX,UINT32_MAX,3};
 NativeSearchResourceObservation value{1,9,2,4,7,1,0,0};
 auto call=[&](std::uint64_t potential=0,std::uint64_t bound=UINT64_MAX){alignas(64) std::uint64_t words[8];std::memcpy(words,&value,sizeof(value));alignas(64) std::uint64_t metadata[8]={queued,used,99};dieroute_native_search_worker_hbm(labels.data(),queue.data(),journal.data(),&parent,words,metadata,8,8,8,1,13,7,1,10,potential,bound,1,&frontier_output,1);queued=metadata[0];used=metadata[1];return NativeObservedRelaxStatus(metadata[2]);};
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
 labels[1]={1,20,1,1,3,0,13,0};
 auto take=[&](){alignas(64) std::uint64_t words[8]{};alignas(64) std::uint64_t metadata[8]={queued,used,99};dieroute_native_search_worker_hbm(labels.data(),queue.data(),journal.data(),&parent,words,metadata,8,8,8,1,13,7,1,10,0,UINT64_MAX,1,&frontier_output,2);queued=metadata[0];assert(metadata[1]==used);return NativeFrontierStatus(metadata[2]);};
 assert(take()==NativeFrontierStatus::current&&queued==0&&frontier_output.node==1&&frontier_output.version==2);
 auto retained=frontier_output;assert(take()==NativeFrontierStatus::empty&&queued==0);assert(std::memcmp(&retained,&frontier_output,sizeof(retained))==0);
 auto command=[&](unsigned operation,unsigned node){parent.node=node;alignas(64) std::uint64_t words[8]{};alignas(64) std::uint64_t metadata[8]={queued,used,99};dieroute_native_search_worker_hbm(labels.data(),queue.data(),journal.data(),&parent,words,metadata,8,8,8,1,13,7,1,10,0,UINT64_MAX,1,&frontier_output,operation);queued=metadata[0];assert(metadata[1]==used);return metadata[2];};
 assert(command(3,1)==std::uint64_t(NativeSearchLabelOpStatus::ok)&&frontier_output.flags==1);
 retained=frontier_output;assert(command(3,7)==std::uint64_t(NativeSearchLabelOpStatus::missing));assert(std::memcmp(&retained,&frontier_output,sizeof(retained))==0);
 parent.cost=0;parent.hops=0;assert(command(4,0)==std::uint64_t(NativeSeedStatus::accepted)&&queued==1&&labels[0].flags==2&&labels[0].version==1);
 assert(command(4,0)==std::uint64_t(NativeSeedStatus::unchanged)&&queued==1);
}
