// Allocation/transfer probe only: synthetic markers, no routing CU launches.
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
void require(bool ok,const char* text){if(!ok)throw std::runtime_error(text);}
std::array<unsigned char,64> marker(unsigned index,U offset){
 std::array<unsigned char,64> value{};U state=(U(index)+1)*UINT64_C(0x9e3779b97f4a7c15)^offset;
 for(auto& b:value){state^=state<<13;state^=state>>7;state^=state<<17;b=static_cast<unsigned char>(state);}
 return value;
}
int main(int argc,char** argv){try{
 require(argc==7,"usage: allocation_probe POLICY_BYTES OFFSET_BYTES ARC_BYTES GROUP BASE CAPACITY");
 std::array<U,3> sizes{};for(unsigned i=0;i<3;++i)sizes[i]=std::stoull(argv[i+1],nullptr,0);
 auto expected_group=std::stoull(argv[4],nullptr,0),base=std::stoull(argv[5],nullptr,0),capacity=std::stoull(argv[6],nullptr,0);
 require(base<=UINT64_MAX-capacity,"group address overflow");
 auto& ctx=dieroute::xrt_host::device_context("DIEROUTE_NET_COMMIT_XCLBIN");
 xrt::kernel kernel(ctx.device,ctx.uuid,"dieroute_net_commit_hbm:{net_commit}",xrt::kernel::cu_access_mode::exclusive);
 std::vector<xrt::bo> buffers;std::array<U,3> addresses{};std::array<std::set<U>,3> positions;
 constexpr U bank=256*1024*1024;
 for(unsigned i=0;i<3;++i){
  auto group=kernel.group_id(i+1);require(group>=0&&U(group)==expected_group,"runtime graph group mismatch");require(sizes[i]>=64,"invalid allocation size");
  buffers.emplace_back(ctx.device,sizes[i],group);addresses[i]=buffers.back().address();require(buffers.back().size()==sizes[i],"allocation size mismatch");
  require(addresses[i]>=base&&addresses[i]<=base+capacity&&sizes[i]<=base+capacity-addresses[i],"allocation outside aggregate group");
  for(unsigned j=0;j<i;++j)require(addresses[i]+sizes[i]<=addresses[j]||addresses[j]+sizes[j]<=addresses[i],"graph BO address alias");
  positions[i].insert(0);positions[i].insert((sizes[i]-64)/64*64);
  for(U boundary=(addresses[i]/bank+1)*bank;boundary<addresses[i]+sizes[i];boundary+=bank){
   U offset=boundary-addresses[i];if(offset>=64)positions[i].insert(offset-64);if(offset<=sizes[i]-64)positions[i].insert(offset);
  }
  std::cout<<"BO index="<<i<<" group="<<group<<" bytes="<<sizes[i]<<" address="<<addresses[i]<<" markers="<<positions[i].size()<<'\n';
 }
 // Writing all objects first also checks that later allocations do not alias
 // previously transferred markers. These are synthetic bytes, not native CSR.
 for(unsigned i=0;i<3;++i)for(auto offset:positions[i]){auto value=marker(i,offset);buffers[i].write(value.data(),value.size(),offset);buffers[i].sync(XCL_BO_SYNC_BO_TO_DEVICE,value.size(),offset);}
 U checks=0;
 for(unsigned i=0;i<3;++i)for(auto offset:positions[i]){
  std::array<unsigned char,64> actual{};buffers[i].sync(XCL_BO_SYNC_BO_FROM_DEVICE,actual.size(),offset);buffers[i].read(actual.data(),actual.size(),offset);require(actual==marker(i,offset),"cross-bank marker mismatch");++checks;
 }
 std::cout<<"ALLOCATION_PROBE_PASS total_bytes="<<sizes[0]+sizes[1]+sizes[2]<<" markers="<<checks<<" kernel_launches=0 full_graph_execution=0\n";
}catch(const std::exception& e){std::cerr<<"ALLOCATION_PROBE_FAIL "<<e.what()<<'\n';return 1;}}
