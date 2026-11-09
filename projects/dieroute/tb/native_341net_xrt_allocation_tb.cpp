// Full configured BO allocation and synthetic readbacks; no CU launches.
#include "../host/xrt_device_context.hpp"
#include <xrt/xrt_kernel.h>
#include <xrt/xrt_bo.h>
#include <array>
#include <cstdint>
#include <iostream>
#include <set>
#include <stdexcept>
#include <vector>
using U=std::uint64_t;
void require(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
unsigned role(unsigned arg){return arg>=1&&arg<=3?0:arg>=8&&arg<=11?1:2;}
std::array<unsigned char,64> marker(unsigned arg,U offset){
 std::array<unsigned char,64> result{};U state=(U(arg)+1)*UINT64_C(0x9e3779b97f4a7c15)^offset;
 for(auto& byte:result){state^=state<<13;state^=state>>7;state^=state<<17;byte=static_cast<unsigned char>(state);}return result;
}
int main(int argc,char** argv){try{
 require(argc==25,"usage: allocation_probe 15_ARG_BYTES GRAPH_GROUP_BASE_CAP AUTH_GROUP_BASE_CAP TRAFFIC_GROUP_BASE_CAP");
 std::array<U,15> sizes{},addresses{};std::array<std::array<U,3>,3> domains{};
 for(unsigned i=0;i<15;++i)sizes[i]=std::stoull(argv[i+1],nullptr,0);
 for(unsigned r=0;r<3;++r)for(unsigned f=0;f<3;++f)domains[r][f]=std::stoull(argv[16+r*3+f],nullptr,0);
 for(const auto& d:domains)require(d[1]<=UINT64_MAX-d[2],"group address overflow");
 auto& ctx=dieroute::xrt_host::device_context("DIEROUTE_NET_COMMIT_XCLBIN");
 xrt::kernel kernel(ctx.device,ctx.uuid,"dieroute_net_commit_hbm:{net_commit}",xrt::kernel::cu_access_mode::exclusive);
 std::vector<xrt::bo> buffers;std::array<std::set<U>,15> positions;constexpr U bank=256*(1<<20);U total=0;
 for(unsigned arg=0;arg<15;++arg){
  const auto& d=domains[role(arg)];auto group=kernel.group_id(arg);require(group>=0&&U(group)==d[0],"runtime role group mismatch");require(sizes[arg]>=64,"probe requires marker-sized BO");
  buffers.emplace_back(ctx.device,sizes[arg],group);addresses[arg]=buffers.back().address();require(buffers.back().size()==sizes[arg],"BO size mismatch");
  require(addresses[arg]>=d[1]&&addresses[arg]<=d[1]+d[2]&&sizes[arg]<=d[1]+d[2]-addresses[arg],"BO outside verified group");
  for(unsigned old=0;old<arg;++old)require(addresses[arg]+sizes[arg]<=addresses[old]||addresses[old]+sizes[old]<=addresses[arg],"BO address alias");
  positions[arg].insert(0);positions[arg].insert((sizes[arg]-64)/64*64);
  for(U boundary=(addresses[arg]/bank+1)*bank;boundary<addresses[arg]+sizes[arg];boundary+=bank){U off=boundary-addresses[arg];if(off>=64)positions[arg].insert(off-64);if(off<=sizes[arg]-64)positions[arg].insert(off);}
  require(total<=UINT64_MAX-sizes[arg],"total size overflow");total+=sizes[arg];std::cout<<"BO arg="<<arg<<" group="<<group<<" bytes="<<sizes[arg]<<" address="<<addresses[arg]<<" markers="<<positions[arg].size()<<'\n';
 }
 for(unsigned arg=0;arg<15;++arg)for(auto off:positions[arg]){auto value=marker(arg,off);buffers[arg].write(value.data(),64,off);buffers[arg].sync(XCL_BO_SYNC_BO_TO_DEVICE,64,off);}
 U checks=0;
 for(unsigned arg=0;arg<15;++arg)for(auto off:positions[arg]){std::array<unsigned char,64> actual{};buffers[arg].sync(XCL_BO_SYNC_BO_FROM_DEVICE,64,off);buffers[arg].read(actual.data(),64,off);require(actual==marker(arg,off),"synthetic marker readback mismatch");++checks;}
 std::cout<<"ALLOCATION_341_PASS total_bytes="<<total<<" buffers=15 markers="<<checks<<" kernel_launches=0 native_graph_uploaded=0\n";
}catch(const std::exception& error){std::cerr<<"ALLOCATION_341_FAIL "<<error.what()<<'\n';return 1;}}
