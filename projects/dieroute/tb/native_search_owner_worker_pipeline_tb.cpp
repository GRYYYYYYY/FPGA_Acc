#include "owner_publish_hbm.hpp"
#include "native_search_hbm_summary_envelope.hpp"
#include "native_search_hbm_seed.hpp"
#include "native_search_hbm_frontier.hpp"
#include "native_search_hbm_relax_observed.hpp"
#include "sparse_label_worker.hpp"
#include <array>
#include <cstring>
#include <cassert>
using namespace dieroute;
extern "C" void dieroute_native_search_owner_envelope_hbm(const std::uint64_t* packet,const std::uint64_t* envelope,std::uint64_t* output_words,std::uint32_t* status,std::uint32_t node,std::uint32_t owner,std::uint32_t worker,std::uint32_t membership,std::uint64_t serial,std::uint64_t session,std::uint64_t epoch,std::uint32_t operation,std::uint64_t ticket,std::uint32_t lane,std::uint32_t slot,std::uint32_t kind);
extern "C" void dieroute_native_search_worker_hbm(dieroute::NativeSearchLabelSlot* labels,dieroute::NativeSearchQueueEntry* queue,dieroute::NativeSearchResourceObservation* journal,const dieroute::NativeSearchLabelSlot* parent,const std::uint64_t* observation_words,std::uint64_t* metadata,std::uint32_t label_capacity,std::uint32_t queue_capacity,std::uint32_t journal_capacity,std::uint32_t dst,std::uint32_t edge,std::uint64_t session,std::uint32_t own,std::uint64_t present,std::uint64_t potential,std::uint64_t max_cost,std::uint32_t credit,dieroute::NativeSearchLabelSlot* frontier_output,std::uint32_t operation);
int main(){
 SummaryWord commands[8]{},owners[1]{},registry[1]{},responses[8]{},updates[8]{},control{},completion{};
 std::uint64_t topology[1]={42|(std::uint64_t(5)<<32)};std::uint32_t dirty[4]{};
 auto packet=[](unsigned kind,std::uint64_t serial,std::uint64_t occupancy,std::uint64_t history,std::uint64_t version){SummaryWord p{};p.w[0]=9;p.w[1]=42|(std::uint64_t(2)<<40)|(std::uint64_t(kind)<<48);p.w[2]=occupancy;p.w[3]=history;p.w[4]=version;p.w[5]=serial;return p;};
 commands[0]=packet(3,16,5,7,11);commands[1].w[0]=owner_install;
 commands[2]=packet(1,17,0,0,0);commands[3].w[0]=owner_subscribe;
 dieroute_owner_publish_hbm(commands,topology,owners,registry,dirty,responses,updates,&control,&completion,1,1,0,3,9,4,4,4,4,0,2,0,0,0,0,4,0,8,~std::uint64_t(0));
 assert(completion.w[6]==0&&completion.w[0]==2&&completion.w[1]==2);
 assert(responses[1].w[0]==summary_ok&&responses[3].w[0]==summary_ok&&responses[3].w[1]==1&&responses[3].w[2]==owner_subscribe);
 NativeSearchResourceObservation journal[4]{};std::uint32_t used=0;std::uint64_t cost=123;
 auto observe=[&](const SummaryWord& p,std::uint64_t serial){return native_search_observe_summary<4>(p.w,42,0,2,5,serial,9,3,journal,4,used,false,3,cost);};
 assert(observe(responses[2],17)==NativeSearchObservationStatus::ok&&used==1&&cost==23);
 assert(journal[0].version==owners[0].w[3]&&journal[0].occupancy==owners[0].w[1]&&journal[0].history==owners[0].w[2]);
 commands[4]=packet(3,18,2,8,12);commands[5].w[0]=owner_install;commands[5].w[2]=11;
 dieroute_owner_publish_hbm(commands,topology,owners,registry,dirty,responses,updates,&control,&completion,1,1,0,3,9,4,4,4,4,2,3,2,2,0,0,4,4,8,~std::uint64_t(0));
 assert(completion.w[6]==0&&completion.w[0]==3&&completion.w[1]==3&&completion.w[2]==1);
 assert(responses[5].w[0]==summary_ok&&updates[1].w[0]==0&&updates[1].w[1]==0&&updates[1].w[2]==12);
 assert(observe(updates[0],1)==NativeSearchObservationStatus::ok&&used==2&&cost==15);
 assert(journal[1].version==12&&journal[1].occupancy==owners[0].w[1]&&journal[1].history==owners[0].w[2]);
 assert(observe(updates[0],2)==NativeSearchObservationStatus::invalid&&used==2&&cost==15);
 NativeSearchResourceObservation bound{};
 auto reply_bind=[&](const SummaryWord& receipt){alignas(64) std::uint64_t words[8];std::memcpy(words,&bound,sizeof(bound));std::uint32_t status=99;dieroute_native_search_owner_envelope_hbm(responses[2].w,receipt.w,words,&status,42,0,2,5,17,9,3,owner_subscribe,1,0,0,1);std::memcpy(&bound,words,sizeof(bound));return NativeSummaryBindingStatus(status);};
 assert(reply_bind(responses[3])==NativeSummaryBindingStatus::ok&&bound.version==11);
 auto retained=bound;
 for(unsigned field=0;field<8;++field){auto bad=responses[3];bad.w[field]^=1;if(field==4)bad.w[4]=2;assert(reply_bind(bad)==NativeSummaryBindingStatus::invalid);assert(std::memcmp(&bound,&retained,sizeof(bound))==0);}
 auto update_bind=[&](const SummaryWord& metadata){alignas(64) std::uint64_t words[8];std::memcpy(words,&bound,sizeof(bound));std::uint32_t status=99;dieroute_native_search_owner_envelope_hbm(updates[0].w,metadata.w,words,&status,42,0,2,5,1,9,3,0,0,0,0,2);std::memcpy(&bound,words,sizeof(bound));return NativeSummaryBindingStatus(status);};
 assert(update_bind(updates[1])==NativeSummaryBindingStatus::ok&&bound.version==12);
 retained=bound;
 for(unsigned field=0;field<8;++field){auto bad=updates[1];bad.w[field]^=1;assert(update_bind(bad)==NativeSummaryBindingStatus::invalid);assert(std::memcmp(&bound,&retained,sizeof(bound))==0);}
 std::array<NativeSearchLabelSlot,1024> labels{};std::array<NativeSearchQueueEntry,1024> queue{};std::array<NativeSearchResourceObservation,1024> reads{};
 NativeSearchLabelSlot seed{3,5,0,1,2,UINT32_MAX,UINT32_MAX,0},current{};std::uint32_t queued=0,read_count=0;
 auto worker=[&](unsigned operation,const NativeSearchLabelSlot& input){alignas(64) std::uint64_t observation[8];std::memcpy(observation,&bound,sizeof(bound));alignas(64) std::uint64_t metadata[8]={queued,read_count,99};dieroute_native_search_worker_hbm(labels.data(),queue.data(),reads.data(),&input,observation,metadata,8,8,8,42,77,9,0,3,0,UINT64_MAX,1,&current,operation);queued=metadata[0];read_count=metadata[1];return metadata[2];};
 assert(worker(4,seed)==std::uint64_t(NativeSeedStatus::accepted)&&queued==1);
 assert(worker(2,seed)==std::uint64_t(NativeFrontierStatus::current)&&queued==0);auto parent=current;
 SparseLabelWorker reference;reference.reset(0,3,64);reference.seed(1,5,5,2,true);reference.pop();reference.close(1);
 auto ref_relax=[&](std::uint64_t cost,std::uint64_t version){auto request=LabelPacket::message(3,version+1,42,LabelOp::relax,0,0);request.value(cost,cost,3,1,77,0,version);assert(reference.receive(request,[](std::uint32_t){return 0U;},true).status()==LabelStatus::accepted);};
 assert(reply_bind(responses[3])==NativeSummaryBindingStatus::ok);assert(worker(1,parent)==std::uint64_t(NativeObservedRelaxStatus::accepted));ref_relax(28,0);
 assert(labels[42%8].cost==28&&read_count==1&&reads[0].version==11);
 auto before_labels=labels;auto before_queue=queue;auto before_reads=reads;auto q_count=queued;
 auto failed=responses[3];failed.w[0]=summary_missing;assert(reply_bind(failed)==NativeSummaryBindingStatus::invalid);
 // A failed binding never dispatches relaxation and preserves all search state.
 assert(std::memcmp(before_labels.data(),labels.data(),sizeof(labels))==0&&std::memcmp(before_queue.data(),queue.data(),sizeof(queue))==0&&std::memcmp(before_reads.data(),reads.data(),sizeof(reads))==0&&queued==q_count&&read_count==1);
 assert(update_bind(updates[1])==NativeSummaryBindingStatus::ok);assert(worker(1,parent)==std::uint64_t(NativeObservedRelaxStatus::accepted));ref_relax(20,1);
 assert(labels[42%8].cost==20&&read_count==2&&reads[1].version==12);
 assert(worker(2,parent)==std::uint64_t(NativeFrontierStatus::current)&&current.node==42&&current.cost==20);auto expected_head=reference.pop();assert(std::get<1>(expected_head)==20);reference.close(42);
 auto saved=current;assert(worker(2,parent)==std::uint64_t(NativeFrontierStatus::skipped)&&queued==0);assert(std::memcmp(&saved,&current,sizeof(saved))==0);
 NativeSearchLabelSlot trace{};trace.epoch=3;trace.node=42;assert(worker(3,trace)==std::uint64_t(NativeSearchLabelOpStatus::ok));auto expected_label=reference.local(42);assert(current.cost==expected_label.cost&&current.hops==expected_label.hops&&current.parent==expected_label.parent&&current.edge==expected_label.edge&&current.version==expected_label.version);
 // Joined handoff: drain update output, advance session, then bootstrap
 // identical resource values/versions. Old packets must fail despite ABA values.
 auto old_reply=responses[2];commands[6]=packet(3,20,5,7,11);commands[6].w[0]=10;commands[7]={};commands[7].w[0]=owner_install;
 commands[0]=packet(1,21,0,0,0);commands[0].w[0]=10;commands[1]={};commands[1].w[0]=owner_subscribe;
 dieroute_owner_publish_hbm(commands,topology,owners,registry,dirty,responses,updates,&control,&completion,1,1,0,3,10,4,4,4,4,3,5,3,3,1,1,4,4,8,~std::uint64_t(0));
 assert(completion.w[6]==0&&completion.w[0]==5&&completion.w[1]==5&&completion.w[2]==1&&owners[0].w[0]==10&&owners[0].w[3]==11);
 assert(responses[7].w[0]==summary_ok&&responses[1].w[0]==summary_ok);
 auto handoff_bind=[&](const SummaryWord& response,std::uint64_t serial){alignas(64) std::uint64_t words[8];std::memcpy(words,&bound,sizeof(bound));std::uint32_t status=99;dieroute_native_search_owner_envelope_hbm(response.w,responses[1].w,words,&status,42,0,2,5,serial,10,4,owner_subscribe,4,0,0,1);std::memcpy(&bound,words,sizeof(bound));return NativeSummaryBindingStatus(status);};
 retained=bound;assert(handoff_bind(old_reply,17)==NativeSummaryBindingStatus::invalid);assert(std::memcmp(&retained,&bound,sizeof(bound))==0);
 assert(handoff_bind(responses[0],21)==NativeSummaryBindingStatus::ok&&bound.session==10&&bound.epoch==4&&bound.version==11&&bound.occupancy==5&&bound.history==7);
}
