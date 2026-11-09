#include "owner_publish_hbm.hpp"
#include "native_search_hbm_summary_envelope.hpp"
#include <cstring>
#include <cassert>
using namespace dieroute;
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
 auto reply_bind=[&](const SummaryWord& receipt){return native_search_bind_owner_reply(responses[2].w,receipt.w,42,0,2,5,17,9,3,owner_subscribe,1,0,0,bound);};
 assert(reply_bind(responses[3])==NativeSummaryBindingStatus::ok&&bound.version==11);
 auto retained=bound;
 for(unsigned field=0;field<8;++field){auto bad=responses[3];bad.w[field]^=1;if(field==4)bad.w[4]=2;assert(reply_bind(bad)==NativeSummaryBindingStatus::invalid);assert(std::memcmp(&bound,&retained,sizeof(bound))==0);}
 auto update_bind=[&](const SummaryWord& metadata){return native_search_bind_owner_update(updates[0].w,metadata.w,42,0,2,5,0,9,3,0,0,bound);};
 assert(update_bind(updates[1])==NativeSummaryBindingStatus::ok&&bound.version==12);
 retained=bound;
 for(unsigned field=0;field<8;++field){auto bad=updates[1];bad.w[field]^=1;assert(update_bind(bad)==NativeSummaryBindingStatus::invalid);assert(std::memcmp(&bound,&retained,sizeof(bound))==0);}
}
