// Component fixture adapter. The production kernel is not linked into this
// host executable. Authority remains in device BOs between ordinary calls.
#include "net_commit_hbm.hpp"
#include "xrt_device_context.hpp"
#include <xrt/xrt_device.h>
#include <xrt/xrt_kernel.h>
#include <xrt/xrt_bo.h>
#include <array>
#include <vector>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <set>
namespace dieroute {namespace {
struct Device {
 xrt_host::DeviceContext& platform=xrt_host::device_context("DIEROUTE_NET_COMMIT_XCLBIN");
 xrt::device& device=platform.device;xrt::uuid uuid=platform.uuid;xrt::kernel kernel;
 std::array<xrt::bo,17> bo;std::array<std::vector<unsigned char>,17> snapshots;
 std::uint64_t calls=0,authority_uploads=0;
 Device(){
  kernel=xrt::kernel(device,uuid,"dieroute_net_commit_sharded_hbm:{net_commit}",xrt::kernel::cu_access_mode::exclusive);
  const std::array<std::size_t,17> sizes={{128,32*8,33*8,64*8,32*16,16*64,16*64,32*16,16*64,16*64,16*64,64*64,8*64,64,128*128,32*64,64}};
  std::cerr<<"XRT net commit groups:";
  for(unsigned i=0;i<17;++i){auto group=kernel.group_id(i);std::cerr<<' '<<group;bo[i]=xrt::bo(device,sizes[i],group);snapshots[i].resize(sizes[i],0);bo[i].write(snapshots[i].data());bo[i].sync(XCL_BO_SYNC_BO_TO_DEVICE);}
  std::cerr<<'\n';
  std::set<int> groups;for(unsigned arg:{0u,1u,8u,9u,10u,11u})groups.insert(kernel.group_id(arg));if(groups.size()!=6)throw std::runtime_error("sharded fixture role alias");
  for(unsigned i=8;i<11;++i)for(unsigned j=8;j<i;++j)if(bo[i].address()<bo[j].address()+bo[j].size()&&bo[j].address()<bo[i].address()+bo[i].size())throw std::runtime_error("owner BO address alias");
 }
 unsigned upload(unsigned i,const void* p,std::size_t bytes,bool authority=false){
  if(bytes>snapshots[i].size())throw std::runtime_error("net commit fixture BO overflow");
  if(!bytes||!std::memcmp(p,snapshots[i].data(),bytes))return 0;
  if(authority)throw std::runtime_error("host attempted to overwrite device sharded net authority");
  bo[i].write(p,bytes,0);bo[i].sync(XCL_BO_SYNC_BO_TO_DEVICE,bytes,0);std::memcpy(snapshots[i].data(),p,bytes);return 1;
 }
 void download(unsigned i,void* p,std::size_t bytes){if(!bytes)return;bo[i].sync(XCL_BO_SYNC_BO_FROM_DEVICE,bytes,0);bo[i].read(p,bytes,0);std::memcpy(snapshots[i].data(),p,bytes);}
};
Device& context(){static Device d;return d;}
}
extern "C" void dieroute_net_commit_hbm(
 const SummaryWord* command,const std::uint64_t* policy,const std::uint64_t* offsets,const std::uint64_t* arcs,
 const std::uint64_t* reads,const SummaryWord* shadows,const SummaryWord* branches,const std::uint64_t* paths,
 SummaryWord* resources,SummaryWord* trees,SummaryWord* nets,SummaryWord* control,SummaryWord* scratch,
 SummaryWord* deltas,SummaryWord* completion,
 std::uint32_t node_count,std::uint64_t arc_count,std::uint32_t dies,std::uint32_t shard_capacity,
 std::uint32_t net_capacity,std::uint32_t tree_capacity,std::uint32_t read_capacity,std::uint32_t shadow_capacity,
 std::uint32_t branch_capacity,std::uint32_t path_capacity,std::uint32_t scratch_capacity,std::uint32_t delta_capacity){
 if(node_count>32||arc_count>64||dies!=3||shard_capacity!=16||net_capacity>8||tree_capacity>64||read_capacity>32||shadow_capacity>16||branch_capacity>16||path_capacity>32||scratch_capacity>128||delta_capacity>32)throw std::runtime_error("net commit XRT component fixture limits");
 auto& d=context();auto& b=d.bo;
 const std::array<std::size_t,8> sizes={{128,node_count*8,(node_count+1)*8,arc_count*8,read_capacity*16,shadow_capacity*64,branch_capacity*64,path_capacity*16}};
 const std::array<const void*,8> inputs={{command,policy,offsets,arcs,reads,shadows,branches,paths}};
 for(unsigned i=0;i<8;++i)d.upload(i,inputs[i],sizes[i]);
 unsigned uploads=0;for(unsigned owner=0;owner<3;++owner)uploads+=d.upload(8+owner,resources+owner*16,16*64,true);
 uploads+=d.upload(11,trees,tree_capacity*64,true);uploads+=d.upload(12,nets,net_capacity*64,true);uploads+=d.upload(13,control,64,true);
 auto run=d.kernel(b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7],b[8],b[9],b[10],b[11],b[12],b[13],b[14],b[15],b[16],node_count,arc_count,dies,shard_capacity,net_capacity,tree_capacity,read_capacity,shadow_capacity,branch_capacity,path_capacity,scratch_capacity,delta_capacity);
 if(run.wait()!=ERT_CMD_STATE_COMPLETED)throw std::runtime_error("sharded net commit CU did not complete");
 for(unsigned owner=0;owner<3;++owner)d.download(8+owner,resources+owner*16,16*64);
 d.download(11,trees,tree_capacity*64);d.download(12,nets,net_capacity*64);d.download(13,control,64);d.download(14,scratch,scratch_capacity*128);d.download(16,completion,64);
 if(completion->w[7]>delta_capacity)throw std::runtime_error("net commit returned invalid delta count");d.download(15,deltas,completion->w[7]*64);
 ++d.calls;d.authority_uploads+=uploads;
 std::cerr<<"XRT net_commit call="<<d.calls<<" op="<<command[0].w[1]<<" status="<<completion->w[0]<<" reads="<<completion->w[2]<<" deltas="<<completion->w[7]<<" authority_uploads="<<uploads<<" total_authority_uploads="<<d.authority_uploads<<'\n';
}
}

namespace dieroute {
xrt::bo& native_commit_sharded_shared_bo(unsigned index){return context().bo.at(index);}
xrt::bo& native_commit_sharded_owner_bo(unsigned owner){if(owner>=3)throw std::runtime_error("invalid owner");return context().bo.at(8+owner);}
bool native_commit_sharded_source_matches(unsigned index,const void* data,std::size_t bytes){auto& d=context();return bytes<=d.snapshots.at(index).size()&&!std::memcmp(data,d.snapshots.at(index).data(),bytes);}
}
namespace dieroute {
std::uint64_t native_commit_call_count(){return context().calls;}
std::uint64_t native_commit_upload_count(){return context().authority_uploads;}
}
