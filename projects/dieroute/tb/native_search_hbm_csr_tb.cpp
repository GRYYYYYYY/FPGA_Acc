#include "native_search_hbm_csr.hpp"
#include <array>
#include <cassert>
#include <cstring>
using namespace dieroute;
int main(){
 std::array<std::uint64_t,5> offsets{0,3,3,3,3};
 std::array<std::uint64_t,3> arcs{1|(std::uint64_t(11)<<32),2|(std::uint64_t(12)<<32),3|(std::uint64_t(13)<<32)};
 std::array<std::uint64_t,4> policy{UINT32_MAX|(std::uint64_t(1)<<32),UINT32_MAX|(std::uint64_t(1)<<32)|(std::uint64_t(1)<<40),8|(std::uint64_t(2)<<32),7|(std::uint64_t(6)<<32)};
 std::uint64_t cursor=0,visited=99;NativeCSRArc output{99,99,99,99};
 auto call=[&](std::uint64_t budget){return native_search_next_arc<4,3>(offsets.data(),arcs.data(),policy.data(),4,3,3,0,7,budget,cursor,visited,output);};
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
