// Sparse endpoint transfers at real directory size; synthetic summary values.
#include "owner_publish_hbm.hpp"
#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace dieroute;
void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
struct State {
 std::array<SummaryWord,16> commands{},responses{},updates{};
 std::vector<SummaryWord> owners,registry,shadows;
 std::vector<std::uint32_t> dirty;
 SummaryWord control{},completion{};std::uint64_t owner_ticket=0,receiver_ticket=0;
 explicit State(std::size_t slots):owners(slots),registry(slots),shadows(slots*4),dirty(65536){}
};
int main(int argc,char** argv){try{
 check(argc==2,"topology container required");std::ifstream f(argv[1],std::ios::binary);std::array<char,64> header{};f.read(header.data(),64);check(bool(f)&&!std::memcmp(header.data(),"FPGAACCP",8),"topology header");std::uint64_t slots=0;std::memcpy(&slots,header.data()+16,8);check(slots==46848,"real native directory size mismatch");std::vector<std::uint64_t> topology(slots);f.read(reinterpret_cast<char*>(topology.data()),slots*8);check(bool(f),"topology payload truncated");
 const auto slot=slots-2;const auto t=topology[slot];const auto mask=std::uint32_t(t>>32);unsigned owner=0;while(!(mask&(1u<<owner)))++owner;unsigned worker=0;while(worker==owner||!(mask&(1u<<worker)))++worker;check(owner<3&&worker<3,"native owner roles");const unsigned lane=2;
 State local(slots),remote(slots);unsigned calls=0,rejected=0;
 auto packet=[&](bool request,std::uint64_t version){SummaryWord p{};p.w[0]=1;p.w[1]=std::uint32_t(t)|(std::uint64_t(owner)<<32)|(std::uint64_t(worker)<<40)|(std::uint64_t(request?1:3)<<48);if(!request){p.w[2]=version;p.w[4]=version;}p.w[5]=1;return p;};
 auto publish=[&](unsigned opcode,std::uint64_t version,std::uint64_t expected){auto pos=(local.owner_ticket&7)*2;local.commands[pos]=packet(false,version);local.commands[pos+1]={};local.commands[pos+1].w[0]=opcode;local.commands[pos+1].w[1]=slot;local.commands[pos+1].w[2]=expected;
  dieroute_owner_publish_hbm(local.commands.data(),topology.data(),local.owners.data(),local.registry.data(),local.dirty.data(),local.responses.data(),local.updates.data(),&local.control,&local.completion,slots,4,owner,3,1,8,8,8,65536,local.owner_ticket,local.owner_ticket+1,local.owner_ticket,local.owner_ticket,0,0,1,0,0,0);++calls;check(!local.completion.w[6]&&!local.responses[pos+1].w[0],"publisher failed");++local.owner_ticket;};
 publish(owner_install,1,0);check(local.owners[slot].w[1]==1&&local.registry[slot].w[0]==1,"high-slot state not read back");
 dieroute_owner_publish_hbm(remote.commands.data(),topology.data(),remote.owners.data(),remote.registry.data(),remote.dirty.data(),remote.responses.data(),remote.updates.data(),&remote.control,&remote.completion,slots,4,worker,3,1,8,8,8,65536,0,0,0,0,0,0,0,0,0,0);++calls;check(!remote.completion.w[6],"receiver bootstrap failed");
 auto receive=[&](unsigned opcode,std::uint64_t version){auto pos=(remote.receiver_ticket&7)*2;remote.commands[pos]=packet(opcode==shadow_inspect,version);remote.commands[pos+1]={};remote.commands[pos+1].w[0]=opcode|(std::uint64_t(lane)<<32);remote.commands[pos+1].w[1]=slot;
  dieroute_summary_hbm(remote.commands.data(),topology.data(),remote.owners.data(),remote.shadows.data(),remote.responses.data(),&remote.completion,slots,4,worker,3,1,8,8,remote.receiver_ticket,remote.receiver_ticket+1,remote.receiver_ticket,remote.receiver_ticket,1);++calls;check(!remote.completion.w[3]&&!remote.responses[pos+1].w[0],"receiver failed");++remote.receiver_ticket;return remote.responses[pos];};
 receive(shadow_receive,1);auto address=lane*slots+slot;check(address!=slot*4+lane,"fixture must distinguish lane-major addressing");check(remote.shadows[address].w[1]==1&&remote.shadows[slot*4+lane].w[0]==0,"lane-major cache state missing");check(receive(shadow_inspect,0).w[2]==1,"cache query disagrees");
 auto saved=local.owners[slot];local.owners[slot].w[1]^=1;bool blocked=false;try{publish(owner_validate,1,0);}catch(const std::runtime_error& e){blocked=std::string(e.what())=="host attempted to overwrite device endpoint state or topology";}local.owners[slot]=saved;check(blocked,"high-slot CPU overwrite accepted");++rejected;publish(owner_validate,1,0);
 publish(owner_install,2,1);receive(shadow_receive,2);check(receive(shadow_inspect,0).w[2]==2,"cache update not reflected");check(calls==8&&rejected==1,"test accounting");std::cout<<"SPARSE_LARGE_PASS slots="<<slots<<" cache_row="<<address<<" kernel_calls="<<calls<<" rejected_overwrites="<<rejected<<'\n';
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
