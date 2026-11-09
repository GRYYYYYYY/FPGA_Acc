// Native-size adapter: one immutable graph per process, guarded device authority.
// The kernel implementation is supplied by the xclbin, not linked on the CPU.
#include "net_commit_hbm.hpp"
#include "xrt_device_context.hpp"
#include <xrt/xrt_kernel.h>
#include <xrt/xrt_bo.h>
#include <algorithm>
#include <array>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>
namespace dieroute {namespace {
using U=std::uint64_t;
void require(bool ok,const char* text){if(!ok)throw std::runtime_error(text);}
std::size_t product(U count,U width){require(count<=std::numeric_limits<std::size_t>::max()/width,"native XRT size overflow");return std::size_t(count*width);}
struct Device {
 xrt_host::DeviceContext& platform=xrt_host::device_context("DIEROUTE_NET_COMMIT_XCLBIN");
 xrt::kernel kernel{platform.device,platform.uuid,"dieroute_net_commit_hbm:{net_commit}",xrt::kernel::cu_access_mode::exclusive};
 std::array<xrt::bo,15> bo;
 std::array<std::size_t,15> allocated{};
 std::array<std::vector<unsigned char>,4> authority;
 std::array<const void*,3> graph{};
 std::array<U,8> configuration{};
 bool initialized=false;
 U calls=0,immutable_bytes_uploaded=0;
 static constexpr std::size_t chunk=16*1024*1024;
 void allocate(unsigned i,std::size_t bytes){
  auto needed=std::max<std::size_t>(1,bytes);if(allocated[i]>=needed)return;
  bo[i]=xrt::bo{};allocated[i]=0;bo[i]=xrt::bo(platform.device,needed,kernel.group_id(i));allocated[i]=needed;
 }
 void upload(unsigned i,const void* source,std::size_t bytes){
  require(bytes<=allocated[i]&&(!bytes||source),"native XRT upload bounds/pointer");auto p=static_cast<const unsigned char*>(source);
  for(std::size_t off=0;off<bytes;off+=chunk){auto n=std::min(chunk,bytes-off);bo[i].write(p+off,n,off);bo[i].sync(XCL_BO_SYNC_BO_TO_DEVICE,n,off);}
 }
 void download(unsigned i,void* target,std::size_t bytes){
  require(bytes<=allocated[i]&&(!bytes||target),"native XRT download bounds/pointer");auto p=static_cast<unsigned char*>(target);
  for(std::size_t off=0;off<bytes;off+=chunk){auto n=std::min(chunk,bytes-off);bo[i].sync(XCL_BO_SYNC_BO_FROM_DEVICE,n,off);bo[i].read(p+off,n,off);}
 }
 void bind(const std::array<U,8>& config,const std::array<std::size_t,15>& sizes,const std::array<const void*,3>& readonly,const std::array<const void*,4>& state,const void* scratch){
  if(initialized){require(config==configuration&&readonly==graph,"native XRT graph/authority dimensions or graph pointers changed");return;}
  require(kernel.group_id(1)==kernel.group_id(2)&&kernel.group_id(1)==kernel.group_id(3),"native graph ports need one allocation group");
  require(kernel.group_id(0)!=kernel.group_id(1)&&kernel.group_id(0)!=kernel.group_id(8)&&kernel.group_id(1)!=kernel.group_id(8),"native traffic/graph/authority bank alias");
  // Check initial authority before any upload; only zero initialization is legal.
  for(unsigned j=0;j<4;++j){require(state[j],"null initial authority");auto p=static_cast<const unsigned char*>(state[j]);require(std::all_of(p,p+sizes[j+8],[](auto b){return b==0;}),"native XRT authority must start zero");}
  for(unsigned i=0;i<15;++i)allocate(i,sizes[i]);
  for(unsigned j=0;j<3;++j){upload(j+1,readonly[j],sizes[j+1]);immutable_bytes_uploaded+=sizes[j+1];}
  for(unsigned j=0;j<4;++j){authority[j].resize(sizes[j+8],0);upload(j+8,authority[j].data(),authority[j].size());}
  upload(12,scratch,sizes[12]);configuration=config;graph=readonly;initialized=true;
  std::cerr<<"XRT native net configured graph_bytes="<<immutable_bytes_uploaded<<" resource_bytes="<<sizes[8]<<" tree_bytes="<<sizes[9]<<'\n';
 }
 void check_authority(const std::array<const void*,4>& state){
  for(unsigned j=0;j<4;++j)require(state[j]&&!std::memcmp(state[j],authority[j].data(),authority[j].size()),"host attempted to overwrite device net authority");
 }
};
Device& context(){static Device instance;return instance;}
}
extern "C" void dieroute_net_commit_hbm(
 const SummaryWord* command,const std::uint64_t* policy,const std::uint64_t* offsets,const std::uint64_t* arcs,
 const std::uint64_t* reads,const SummaryWord* shadows,const SummaryWord* branches,const std::uint64_t* paths,
 SummaryWord* resources,SummaryWord* trees,SummaryWord* nets,SummaryWord* control,SummaryWord* scratch,
 SummaryWord* deltas,SummaryWord* completion,
 std::uint32_t node_count,std::uint64_t arc_count,std::uint32_t dies,std::uint32_t shard_capacity,
 std::uint32_t net_capacity,std::uint32_t tree_capacity,std::uint32_t read_capacity,std::uint32_t shadow_capacity,
 std::uint32_t branch_capacity,std::uint32_t path_capacity,std::uint32_t scratch_capacity,std::uint32_t delta_capacity){
 require(node_count&&dies&&dies<=3&&shard_capacity&&!(shard_capacity&(shard_capacity-1))&&net_capacity&&tree_capacity&&read_capacity&&shadow_capacity&&branch_capacity&&path_capacity&&scratch_capacity&&delta_capacity,"invalid native XRT dimensions");
 const std::array<std::size_t,15> sizes={128,product(node_count,8),product(U(node_count)+1,8),product(arc_count,8),product(read_capacity,16),product(shadow_capacity,64),product(branch_capacity,64),product(path_capacity,16),product(U(dies)*shard_capacity,64),product(tree_capacity,64),product(net_capacity,64),64,product(scratch_capacity,128),product(delta_capacity,64),64};
 auto& d=context();auto& b=d.bo;std::array<const void*,4> state={resources,trees,nets,control};
 d.bind({node_count,arc_count,dies,shard_capacity,net_capacity,tree_capacity,scratch_capacity,delta_capacity},sizes,{policy,offsets,arcs},state,scratch);d.check_authority(state);
 const std::array<const void*,5> transient={command,reads,shadows,branches,paths};const std::array<unsigned,5> indexes={0,4,5,6,7};
 for(unsigned j=0;j<5;++j){auto i=indexes[j];d.allocate(i,sizes[i]);d.upload(i,transient[j],sizes[i]);}
 auto run=d.kernel(b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7],b[8],b[9],b[10],b[11],b[12],b[13],b[14],node_count,arc_count,dies,shard_capacity,net_capacity,tree_capacity,read_capacity,shadow_capacity,branch_capacity,path_capacity,scratch_capacity,delta_capacity);
 require(run.wait()==ERT_CMD_STATE_COMPLETED,"native net CU did not complete");d.download(14,completion,64);require(completion->w[7]<=delta_capacity,"native delta count overflow");
 std::array<void*,4> outputs={resources,trees,nets,control};
 for(unsigned j=0;j<4;++j){d.download(j+8,outputs[j],sizes[j+8]);std::memcpy(d.authority[j].data(),outputs[j],sizes[j+8]);}
 d.download(12,scratch,sizes[12]);d.download(13,deltas,product(completion->w[7],64));++d.calls;
 std::cerr<<"XRT net_commit call="<<d.calls<<" op="<<command[0].w[1]<<" status="<<completion->w[0]<<" reads="<<completion->w[2]<<" deltas="<<completion->w[7]<<" authority_uploads=0 total_authority_uploads=0\n";
}
}
