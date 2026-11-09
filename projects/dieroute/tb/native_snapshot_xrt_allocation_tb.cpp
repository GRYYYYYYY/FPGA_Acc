// Complete bounded buffer allocation and markers; no search or commit launches.
#include "../host/xrt_device_context.hpp"
#include <xrt/xrt_kernel.h>
#include <xrt/xrt_bo.h>
#include <array>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
#include <vector>
using U=std::uint64_t;
void require(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
std::array<unsigned char,64> marker(unsigned id,U offset){std::array<unsigned char,64> b{};U state=(U(id)+1)*UINT64_C(0x9e3779b97f4a7c15)^offset;for(auto& v:b){state^=state<<13;state^=state>>7;state^=state<<17;v=state;}return b;}
int main(int argc,char** argv){try{
 require(argc==11,"usage: allocation PLAN GRAPH_GROUP_BASE_CAP AUTH_GROUP_BASE_CAP SCRATCH_GROUP_BASE_CAP");
 std::array<std::array<U,3>,3> domains{};for(unsigned r=0;r<3;++r)for(unsigned f=0;f<3;++f)domains[r][f]=std::stoull(argv[2+r*3+f],nullptr,0);
 auto& ctx=dieroute::xrt_host::device_context("DIEROUTE_NET_COMMIT_XCLBIN");std::vector<xrt::kernel> kernels;
 for(auto name:{"dieroute_native_snapshot_search_hbm:{snapshot_search}","dieroute_native_search_worker_hbm:{search_worker}","dieroute_net_commit_hbm:{net_commit}"})kernels.emplace_back(ctx.device,ctx.uuid,name,xrt::kernel::cu_access_mode::exclusive);
 std::ifstream plan(argv[1]);require(bool(plan),"plan open");std::vector<xrt::bo> buffers;std::vector<std::set<U>> positions;std::vector<U> addresses,sizes;std::set<std::pair<unsigned,unsigned>> bindings;U total=0;std::string line;
 while(std::getline(plan,line)){if(line.empty())continue;std::istringstream s(line);std::string name;U bytes;unsigned role,count;s>>name>>bytes>>role>>count;require(bool(s)&&role<3&&bytes>=64&&count,"plan row");auto domain=domains[role];require(domain[1]<=UINT64_MAX-domain[2],"domain overflow");
  for(unsigned i=0;i<count;++i){unsigned kernel,arg;s>>kernel>>arg;require(bool(s)&&kernel<3&&bindings.emplace(kernel,arg).second,"argument binding");require(U(kernels[kernel].group_id(arg))==domain[0],"shared runtime group mismatch");}
  buffers.emplace_back(ctx.device,bytes,domain[0]);auto address=buffers.back().address();require(buffers.back().size()==bytes&&address>=domain[1]&&address<=domain[1]+domain[2]&&bytes<=domain[1]+domain[2]-address,"allocation outside verified group");
  for(unsigned i=0;i<addresses.size();++i)require(address+bytes<=addresses[i]||addresses[i]+sizes[i]<=address,"allocation alias");addresses.push_back(address);sizes.push_back(bytes);positions.emplace_back();auto& marks=positions.back();marks.insert(0);marks.insert((bytes-64)/64*64);
  constexpr U bank=256*(1<<20);for(U boundary=(address/bank+1)*bank;boundary<address+bytes;boundary+=bank){auto off=boundary-address;if(off>=64)marks.insert(off-64);if(off<=bytes-64)marks.insert(off);}total+=bytes;
  std::cout<<"BO name="<<name<<" bytes="<<bytes<<" group="<<domain[0]<<" address="<<address<<" markers="<<marks.size()<<'\n';
 }
 require(bindings.size()==35&&buffers.size()==26,"complete pointer and buffer coverage");
 for(unsigned i=0;i<buffers.size();++i)for(auto off:positions[i]){auto b=marker(i,off);buffers[i].write(b.data(),64,off);buffers[i].sync(XCL_BO_SYNC_BO_TO_DEVICE,64,off);}
 U checks=0;for(unsigned i=0;i<buffers.size();++i)for(auto off:positions[i]){std::array<unsigned char,64> b{};buffers[i].sync(XCL_BO_SYNC_BO_FROM_DEVICE,64,off);buffers[i].read(b.data(),64,off);require(b==marker(i,off),"marker readback mismatch");++checks;}
 std::cout<<"SNAPSHOT_ALLOCATION_PASS buffers=26 pointer_arguments=35 total_bytes="<<total<<" markers="<<checks<<" kernel_launches=0 native_graph_uploaded=0\n";
}catch(const std::exception& e){std::cerr<<"SNAPSHOT_ALLOCATION_FAIL "<<e.what()<<'\n';return 1;}}
