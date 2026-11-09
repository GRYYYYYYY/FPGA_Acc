#include "net_commit_fixture.hpp"
#include "native_search_hbm_snapshot_search.hpp"
#include "native_search_hbm_seed.hpp"
using namespace commit_test;
extern "C" void dieroute_native_snapshot_search_hbm(const std::uint64_t* offsets,const std::uint64_t* arcs,const std::uint64_t* policy,const dieroute::SummaryWord* resources,const std::uint64_t* authority_control,const std::uint64_t* potential,dieroute::NativeSearchLabelSlot* labels,dieroute::NativeSearchQueueEntry* queue,dieroute::NativeSearchResourceObservation* journal,std::uint64_t* metadata,const std::uint64_t* configuration,std::uint64_t* result_words,std::uint64_t* goal_words);
int main(){
 for(unsigned scenario=0;scenario<9;++scenario){Fixture f;f.request(commit_initialize);f.run();f.start(0,10,0);f.start(1,20,4);f.start(2,30,8);
  f.request(commit_proposal,0,10);f.footprint({1,3,5,7,9});f.branch(0,{1,3,5,7,9},0);f.run();f.request(commit_proposal,1,20);f.footprint({6,7});f.branch(4,{6,7},1);f.run();
  if(scenario==5){f.request(commit_negotiate);f.command[0].w[7]=UINT64_MAX-1;f.command[1].w[4]=2;f.run();check(f.resource(7)->w[2]==UINT64_MAX-1,"overflow authority producer");}
  std::array<NativeSearchLabelSlot,1024> labels{};std::array<NativeSearchQueueEntry,1024> queue{};std::array<NativeSearchResourceObservation,1024> journal{};std::uint32_t queued=0;NativeSearchLabelSlot seed{3,0,0,8,0,UINT32_MAX,UINT32_MAX,0},output{};check(native_search_seed<1024>(labels.data(),16,queue.data(),1024,queued,seed,0,UINT64_MAX,true,output)==NativeSeedStatus::accepted,"seed");
  alignas(64) std::uint64_t configuration[16]={12,f.arc_count,3,16,64,30,7,1,f.control.w[1],3,UINT64_MAX,UINT32_MAX,16,1024,1024,0},metadata[8]={queued,0,1},words[8]{},goal[8]={99,99,99,99,99,99,99,99},potential[12]{};
  NativeSnapshotStatus expected=NativeSnapshotStatus::invalid;
  if(scenario==0)configuration[8]++;
  if(scenario==1)configuration[7]=2;
  if(scenario==2)configuration[0]=std::uint64_t(UINT32_MAX)+1;
  if(scenario==3)configuration[12]=0;
  if(scenario==4)metadata[0]=1025;
  if(scenario==5)expected=NativeSnapshotStatus::overflow;
  if(scenario==6){configuration[14]=1;f.resources[2*16+11].w[0]=2;expected=NativeSnapshotStatus::journal_full;}
  if(scenario==7)f.arcs[f.offsets[8]]=12|(std::uint64_t(16)<<32);
  if(scenario==8)f.resources[2*16+10].w[0]=2;
  auto authority=f.state();auto old_policy=f.policy;auto old_arcs=f.arcs;auto old_offsets=f.offsets;auto old_labels=labels;auto old_queue=queue;auto old_journal=journal;
  dieroute_native_snapshot_search_hbm(f.offsets.data(),f.arcs.data(),f.policy.data(),f.resources.data(),f.control.w,potential,labels.data(),queue.data(),journal.data(),metadata,configuration,words,goal);
  check(words[0]==std::uint64_t(expected),"failure status");check(authority==f.state()&&old_policy==f.policy&&old_arcs==f.arcs&&old_offsets==f.offsets,"failed search mutated authority/graph");for(auto value:goal)check(value==99,"failure overwrote goal");
  if(scenario<5){check(!std::memcmp(old_labels.data(),labels.data(),sizeof(labels))&&!std::memcmp(old_queue.data(),queue.data(),sizeof(queue))&&!std::memcmp(old_journal.data(),journal.data(),sizeof(journal)),"invalid preflight changed scratch");}
  if(scenario==5)check(metadata[1]==3&&journal[2].node==7&&journal[2].history==UINT64_MAX-1,"overflow observation lost");
  if(scenario==8)check(metadata[1]==0,"invalid resource produced a cost observation");
  if(scenario==6)check(metadata[1]==1&&journal[0].node==10,"journal credit did not precede owner fetch");
 }
}
