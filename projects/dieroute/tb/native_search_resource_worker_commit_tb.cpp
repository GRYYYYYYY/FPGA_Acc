#include "net_commit_fixture.hpp"
#include "native_search_hbm_resource.hpp"
#include "native_search_hbm_relax_observed.hpp"
#include "native_search_hbm_seed.hpp"
#include "native_search_hbm_frontier.hpp"
using namespace commit_test;
extern "C" void dieroute_native_search_resource_hbm(const std::uint64_t* policy,const dieroute::SummaryWord* resources,const std::uint64_t* control_words,std::uint64_t* output_words,std::uint32_t* status,std::uint32_t nodes,std::uint32_t dies,std::uint32_t shard_capacity,std::uint32_t tree_capacity,std::uint32_t node,std::uint64_t session,std::uint64_t revision,std::uint64_t epoch);
extern "C" void dieroute_native_search_worker_hbm(dieroute::NativeSearchLabelSlot* labels,dieroute::NativeSearchQueueEntry* queue,dieroute::NativeSearchResourceObservation* journal,const dieroute::NativeSearchLabelSlot* parent,const std::uint64_t* observation_words,std::uint64_t* metadata,std::uint32_t label_capacity,std::uint32_t queue_capacity,std::uint32_t journal_capacity,std::uint32_t dst,std::uint32_t edge,std::uint64_t session,std::uint32_t own,std::uint64_t present,std::uint64_t potential,std::uint64_t max_cost,std::uint32_t credit,dieroute::NativeSearchLabelSlot* frontier_output,std::uint32_t operation);
int main(){Fixture f;f.request(commit_initialize);f.run();f.start(0,10,0);f.start(1,20,4);f.start(2,30,8);
 f.request(commit_proposal,0,10);f.footprint({1,3,5,7,9});f.branch(0,{1,3,5,7,9},0);f.run();
 f.request(commit_proposal,1,20);f.footprint({6,7});f.branch(4,{6,7},1);f.run();
 std::array<NativeSearchLabelSlot,1024> labels{};std::array<NativeSearchQueueEntry,1024> queue{};std::array<NativeSearchResourceObservation,1024> journal{};
 std::uint32_t queued=0,used=0;std::uint64_t epoch=3;NativeSearchLabelSlot output{};alignas(64) std::uint64_t observation[8]{};
 auto read=[&](unsigned node){auto before=f.state();std::uint32_t status=99;dieroute_native_search_resource_hbm(f.policy.data(),f.resources.data(),f.control.w,observation,&status,12,3,16,64,node,1,f.control.w[1],epoch);check(status!=std::uint32_t(NativeResourceReadStatus::invalid)&&before==f.state(),"authority read failed/mutated state");};
 auto worker=[&](unsigned operation,const NativeSearchLabelSlot& parent,unsigned dst=0,unsigned edge=0){alignas(64) std::uint64_t metadata[8]={queued,used,99};dieroute_native_search_worker_hbm(labels.data(),queue.data(),journal.data(),&parent,observation,metadata,16,16,16,dst,edge,1,0,f.control.w[2],0,UINT64_MAX,1,&output,operation);queued=metadata[0];used=metadata[1];return metadata[2];};
 auto search=[&](std::uint64_t expected){NativeSearchLabelSlot seed{epoch,0,0,8,0,UINT32_MAX,UINT32_MAX,0};check(worker(4,seed)==0,"seed");check(worker(2,seed)==0&&output.node==8,"root");auto parent=output;read(10);check(worker(1,parent,10,f.edges.at({8,10}))==0,"first arc");check(worker(2,seed)==0&&output.node==10&&output.cost==1,"intermediate");parent=output;read(7);check(worker(1,parent,7,f.edges.at({10,7}))==0,"shared arc");check(worker(2,seed)==0&&output.node==7&&output.cost==expected&&output.hops==2,"dynamic route cost");};
 auto validate=[&](unsigned index,bool fresh){f.request(commit_validate,2,30);f.command[1].w[0]=2;f.reads[0]=7;f.reads[1]=journal[index+1].version;f.reads[2]=10;f.reads[3]=journal[index].version;f.command[1].w[1]=1;f.shadows[0].w[0]=7;f.shadows[0].w[1]=2;f.shadows[0].w[2]=journal[index+1].occupancy;f.shadows[0].w[3]=journal[index+1].history;f.shadows[0].w[4]=journal[index+1].version;f.run(fresh?commit_ok:commit_conflict);};
 search(4);check(used==2&&journal[1].occupancy==2&&journal[1].history==0,"initial observations");validate(0,true);
 f.request(commit_negotiate);f.command[0].w[7]=1;f.command[1].w[4]=2;f.run();validate(0,false);check(f.completion.w[3]==1&&f.completion.w[4]==1,"stale consumed version/history not rejected");
 // Coordinator starts a fresh search epoch; authority buffers remain intact.
 epoch=4;queued=0;search(7);check(used==4&&journal[3].history==1&&journal[3].version>journal[1].version,"fresh observations");validate(2,true);
}
