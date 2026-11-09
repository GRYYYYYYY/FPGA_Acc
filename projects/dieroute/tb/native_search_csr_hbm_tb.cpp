#include "native_search_hbm_csr.hpp"
#include <array>
#include <cassert>
#include <cstring>
using namespace dieroute;
extern "C" void dieroute_native_search_csr_hbm(const std::uint64_t*,const std::uint64_t*,const std::uint64_t*,std::uint64_t*,std::uint64_t*,std::uint32_t,std::uint64_t,std::uint32_t,std::uint32_t,std::uint32_t,std::uint64_t);
int main(){
 std::array<std::uint64_t,1025> offsets{0,3,3,3,3};
 std::array<std::uint64_t,1024> arcs{1|(std::uint64_t(11)<<32),2|(std::uint64_t(12)<<32),3|(std::uint64_t(13)<<32)};
 std::array<std::uint64_t,1024> policy{UINT32_MAX|(std::uint64_t(1)<<32),UINT32_MAX|(std::uint64_t(1)<<32)|(std::uint64_t(1)<<40),8|(std::uint64_t(2)<<32),7|(std::uint64_t(6)<<32)};
 std::uint64_t cursor=0,visited=99;NativeCSRArc output{99,99,99,99};
 auto call=[&](std::uint64_t budget){alignas(64) std::uint64_t metadata[8]={cursor,visited,99};alignas(64) std::uint64_t words[8]={output.node,output.edge,output.owner,output.membership,44,45,46,47};dieroute_native_search_csr_hbm(offsets.data(),arcs.data(),policy.data(),metadata,words,4,3,3,0,7,budget);cursor=metadata[0];visited=metadata[1];output={std::uint32_t(words[0]),std::uint32_t(words[1]),std::uint32_t(words[2]),std::uint32_t(words[3])};for(unsigned i=4;i<8;++i)assert(words[i]==40+i);return NativeCSRStatus(metadata[2]);};
 assert(call(1)==NativeCSRStatus::budget&&cursor==1&&visited==1&&output.node==99);
 assert(call(1)==NativeCSRStatus::budget&&cursor==2&&visited==1&&output.node==99);
 assert(call(1)==NativeCSRStatus::arc&&cursor==3&&visited==1&&output.node==3&&output.edge==13&&output.owner==1&&output.membership==6);
 auto retained=output;assert(call(1)==NativeCSRStatus::end&&cursor==3&&visited==0&&std::memcmp(&retained,&output,sizeof(output))==0);
 cursor=0;assert(call(0)==NativeCSRStatus::budget&&cursor==0&&visited==0);
 for(unsigned fault=0;fault<4;++fault){auto old_arcs=arcs;auto old_policy=policy;cursor=2;visited=99;
  if(fault==0)arcs[2]=4;
  if(fault==1)arcs[2]=3|(std::uint64_t(UINT32_MAX)<<32);
  if(fault==2)policy[3]=7;
  if(fault==3)policy[3]|=std::uint64_t(1)<<41;
  assert(call(1)==NativeCSRStatus::invalid&&cursor==2&&visited==99&&std::memcmp(&retained,&output,sizeof(output))==0);arcs=old_arcs;policy=old_policy;
 }
}
