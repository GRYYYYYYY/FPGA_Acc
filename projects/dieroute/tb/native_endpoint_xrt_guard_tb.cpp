// Device endpoint state and immutable topology must reject host modifications.
#include "owner_publish_hbm.hpp"
#include <array>
#include <iostream>
#include <stdexcept>
#include <string>
using namespace dieroute;
void check(bool ok,const char* text){if(!ok)throw std::runtime_error(text);}
struct State {
 std::array<SummaryWord,4> commands{},responses{},updates{};
 SummaryWord owner{},registry{},control{},completion{},shadow{};
 std::uint32_t dirty=0;std::uint64_t ticket=0;
};
int main(){try{
 std::uint64_t topology=99|(UINT64_C(3)<<32);State local,remote;unsigned calls=0,rejected=0;
 auto packet=[](bool lookup){SummaryWord p{};p.w[0]=1;p.w[1]=99|(UINT64_C(1)<<40)|(std::uint64_t(lookup?1:3)<<48);if(!lookup){p.w[2]=1;p.w[4]=1;}p.w[5]=1;return p;};
 auto owner=[&](std::uint32_t opcode){auto pos=(local.ticket&1)*2;local.commands[pos]=packet(false);local.commands[pos+1]={};local.commands[pos+1].w[0]=opcode;
  dieroute_owner_publish_hbm(local.commands.data(),&topology,&local.owner,&local.registry,&local.dirty,local.responses.data(),local.updates.data(),&local.control,&local.completion,1,1,0,3,1,2,2,2,1,local.ticket,local.ticket+1,local.ticket,local.ticket,0,0,1,0,0,0);++calls;
  check(local.completion.w[6]==0&&local.responses[pos+1].w[0]==0,"owner receipt failed");++local.ticket;
 };
 owner(owner_install);check(local.owner.w[1]==1&&local.owner.w[3]==1,"owner install missing");
 for(auto* word:std::array<SummaryWord*,3>{&local.owner,&local.registry,&local.control}){auto saved=*word;word->w[1]^=1;bool blocked=false;try{owner(owner_validate);}catch(const std::runtime_error& e){blocked=std::string(e.what())=="host attempted to overwrite device endpoint state or topology";}*word=saved;check(blocked,"CPU state write accepted");++rejected;owner(owner_validate);}
 local.dirty^=1;bool blocked=false;try{owner(owner_validate);}catch(const std::runtime_error& e){blocked=std::string(e.what())=="host attempted to overwrite device endpoint state or topology";}local.dirty^=1;check(blocked,"CPU dirty queue write accepted");++rejected;owner(owner_validate);
 dieroute_owner_publish_hbm(remote.commands.data(),&topology,&remote.owner,&remote.registry,&remote.dirty,remote.responses.data(),remote.updates.data(),&remote.control,&remote.completion,1,1,1,3,1,2,2,2,1,0,0,0,0,0,0,0,0,0,0);++calls;check(remote.completion.w[6]==0,"remote bootstrap failed");
 auto receiver=[&](std::uint32_t opcode){auto pos=(remote.ticket&1)*2;remote.commands[pos]=packet(opcode==shadow_inspect);remote.commands[pos+1]={};remote.commands[pos+1].w[0]=opcode;
  dieroute_summary_hbm(remote.commands.data(),&topology,&remote.owner,&remote.shadow,remote.responses.data(),&remote.completion,1,1,1,3,1,2,2,remote.ticket,remote.ticket+1,remote.ticket,remote.ticket,1);++calls;if(remote.completion.w[3]||remote.responses[pos+1].w[0])std::cerr<<"receiver status="<<remote.responses[pos+1].w[0]<<" launch_error="<<remote.completion.w[3]<<'\n';check(remote.completion.w[3]==0&&remote.responses[pos+1].w[0]==0,"receiver receipt failed");++remote.ticket;
 };
 receiver(shadow_receive);check(remote.shadow.w[1]==1&&remote.shadow.w[3]==1,"delivery missing");auto saved=remote.shadow;remote.shadow.w[1]^=1;blocked=false;try{receiver(shadow_inspect);}catch(const std::runtime_error& e){blocked=std::string(e.what())=="host attempted to overwrite device endpoint state or topology";}remote.shadow=saved;check(blocked,"CPU receiver shadow write accepted");++rejected;receiver(shadow_inspect);check(remote.responses[((remote.ticket-1)&1)*2].w[2]==1,"guard changed cached value");
 check(calls==8&&rejected==5,"endpoint guard accounting");std::cout<<"NATIVE_ENDPOINT_GUARD_PASS kernel_calls="<<calls<<" rejected_state_writes="<<rejected<<'\n';
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
