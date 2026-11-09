#include "native_search_hbm_snapshot_search_sharded.hpp"
#include <vector>
#include <array>
#include <cstring>
#include <stdexcept>
#include <iostream>
using namespace dieroute;
using U=std::uint64_t;
extern "C" void dieroute_native_snapshot_search_flat_reference(const U*,const U*,const U*,const SummaryWord*,const U*,const U*,NativeSearchLabelSlot*,NativeSearchQueueEntry*,NativeSearchResourceObservation*,U*,const U*,U*,U*);
extern "C" void dieroute_native_snapshot_search_sharded_hbm(const U*,const U*,const U*,const SummaryWord*,const SummaryWord*,const SummaryWord*,const U*,const U*,NativeSearchLabelSlot*,NativeSearchQueueEntry*,NativeSearchResourceObservation*,U*,const U*,U*,U*);
namespace {unsigned calls=0;struct Count{~Count(){std::cout<<"SHARDED_SEARCH_DIFFERENTIAL calls="<<calls<<'\n';}} count;
void check(bool v){if(!v)throw std::runtime_error("banked whole-search byte differential failed");}}
extern "C" void dieroute_native_snapshot_search_hbm(const U* offsets,const U* arcs,const U* policy,const SummaryWord* resources,const U* control,const U* potential,NativeSearchLabelSlot* labels,NativeSearchQueueEntry* queue,NativeSearchResourceObservation* journal,U* metadata,const U* configuration,U* result,U* goal){
 check(configuration[2]==3&&configuration[3]<=16&&configuration[12]<=1024&&configuration[13]<=1024&&configuration[14]<=1024);
 std::vector<NativeSearchLabelSlot> ref_labels(labels,labels+1024);std::vector<NativeSearchQueueEntry> ref_queue(queue,queue+1024);std::vector<NativeSearchResourceObservation> ref_journal(journal,journal+1024);std::array<U,8> ref_metadata{},ref_result{},ref_goal{};
 std::memcpy(ref_metadata.data(),metadata,64);std::memcpy(ref_result.data(),result,64);std::memcpy(ref_goal.data(),goal,64);
 std::array<std::array<SummaryWord,24>,3> banks{};SummaryWord sentinel{};for(auto& w:sentinel.w)w=UINT64_C(0xa5912f73d26be048);
 for(unsigned owner=0;owner<3;++owner){banks[owner].fill(sentinel);std::memcpy(banks[owner].data()+4,resources+owner*configuration[3],configuration[3]*64);}auto before=banks;
 dieroute_native_snapshot_search_flat_reference(offsets,arcs,policy,resources,control,potential,ref_labels.data(),ref_queue.data(),ref_journal.data(),ref_metadata.data(),configuration,ref_result.data(),ref_goal.data());
 dieroute_native_snapshot_search_sharded_hbm(offsets,arcs,policy,banks[0].data()+4,banks[1].data()+4,banks[2].data()+4,control,potential,labels,queue,journal,metadata,configuration,result,goal);
 check(!std::memcmp(banks.data(),before.data(),sizeof(banks)));check(!std::memcmp(labels,ref_labels.data(),ref_labels.size()*64));check(!std::memcmp(queue,ref_queue.data(),ref_queue.size()*64));check(!std::memcmp(journal,ref_journal.data(),ref_journal.size()*64));check(!std::memcmp(metadata,ref_metadata.data(),64));check(!std::memcmp(result,ref_result.data(),64));check(!std::memcmp(goal,ref_goal.data(),64));++calls;
}
