// Joint owner publisher + receiver fixture adapter. No CPU kernel is linked.
// Callers serialize access to each logical die and own BOs between launches.
#include "owner_publish_hbm.hpp"
#include "xrt_device_context.hpp"
#include <xrt/xrt_device.h>
#include <xrt/xrt_kernel.h>
#include <xrt/xrt_bo.h>
#include <array>
#include <memory>
#include <mutex>
#include <vector>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <stdexcept>
namespace dieroute {
namespace {
struct Device {
    xrt_host::DeviceContext& platform=xrt_host::device_context("DIEROUTE_OWNER_PUBLISH_XCLBIN");
    xrt::device& device=platform.device;xrt::uuid uuid=platform.uuid;
    std::mutex log_mutex;
    struct Die {std::unique_ptr<xrt::kernel> owner,receiver;std::array<xrt::bo,13> buffers;std::array<std::vector<unsigned char>,13> snapshots;};
    std::array<Die,3> dies;
    Device(){
        for(unsigned d=0;d<3;++d){auto& die=dies[d];
            die.owner=std::make_unique<xrt::kernel>(device,uuid,"dieroute_owner_publish_hbm:{owner_die"+std::to_string(d)+"}",xrt::kernel::cu_access_mode::exclusive);
            die.receiver=std::make_unique<xrt::kernel>(device,uuid,"dieroute_summary_hbm:{summary_die"+std::to_string(d)+"}",xrt::kernel::cu_access_mode::exclusive);
            for(unsigned arg:{1,2})if(die.owner->group_id(arg)!=die.receiver->group_id(arg))throw std::runtime_error("owner/receiver shared BO bank mismatch");
            if(die.owner->group_id(2)==die.owner->group_id(3)||die.owner->group_id(2)==die.receiver->group_id(3))throw std::runtime_error("owner/registry/cache bank alias");
            const std::array<unsigned,13> sizes={{32*64,16*8,16*64,16*64,16*4,32*64,32*64,64,64,32*64,64*64,32*64,64}};
            const std::array<unsigned,4> receiver_args={{0,3,4,5}};
            std::cerr<<"XRT shared die="<<d<<" groups:";
            for(unsigned i=0;i<13;++i){auto group=i<9?die.owner->group_id(i):die.receiver->group_id(receiver_args[i-9]);std::cerr<<' '<<group;die.buffers[i]=xrt::bo(device,sizes[i],group);die.snapshots[i].resize(sizes[i],0);die.buffers[i].write(die.snapshots[i].data());die.buffers[i].sync(XCL_BO_SYNC_BO_TO_DEVICE);}
            std::cerr<<'\n';
        }
    }
    unsigned upload(unsigned d,unsigned b,const void* p,std::size_t bytes){auto& die=dies[d];if(bytes>die.snapshots[b].size())throw std::runtime_error("fixture BO overflow");if(!std::memcmp(die.snapshots[b].data(),p,bytes))return 0;die.buffers[b].write(p,bytes,0);die.buffers[b].sync(XCL_BO_SYNC_BO_TO_DEVICE,bytes,0);std::memcpy(die.snapshots[b].data(),p,bytes);return 1;}
    void download(unsigned d,unsigned b,void* p,std::size_t bytes){auto& die=dies[d];die.buffers[b].sync(XCL_BO_SYNC_BO_FROM_DEVICE,bytes,0);die.buffers[b].read(p,bytes,0);std::memcpy(die.snapshots[b].data(),p,bytes);}
};
Device& context(){static Device d;return d;}
void limits(unsigned slots,unsigned lanes,unsigned die,unsigned command,unsigned response){if(!slots||slots>16||!lanes||lanes>4||die>=3||!command||command>16||!response||response>16)throw std::runtime_error("XRT fixture allocation limits");}
}
extern "C" void dieroute_owner_publish_hbm(
    const SummaryWord* commands,const std::uint64_t* topology,
    SummaryWord* owners,SummaryWord* registry,std::uint32_t* dirty_queue,
    SummaryWord* responses,SummaryWord* updates,SummaryWord* queue_control,SummaryWord* completion,
    std::uint32_t slots,std::uint32_t lanes,std::uint32_t die,std::uint32_t dies,
    std::uint64_t session,std::uint32_t command_capacity,std::uint32_t response_capacity,
    std::uint32_t update_capacity,std::uint32_t dirty_capacity,
    std::uint64_t command_read,std::uint64_t command_write,
    std::uint64_t response_read,std::uint64_t response_write,
    std::uint64_t update_read,std::uint64_t update_write,
    std::uint32_t max_commands,std::uint32_t max_updates,std::uint32_t max_visits,
    std::uint64_t subscriber_filter){
    limits(slots,lanes,die,command_capacity,response_capacity);if(!update_capacity||update_capacity>16||!dirty_capacity||dirty_capacity>16)throw std::runtime_error("publisher fixture queue allocation limits");auto& ctx=context();auto& d=ctx.dies[die];auto& b=d.buffers;
    const std::array<std::size_t,9> sizes={{command_capacity*128,slots*8,slots*64,slots*64,dirty_capacity*4,response_capacity*128,update_capacity*128,64,64}};
    const std::array<const void*,9> input={{commands,topology,owners,registry,dirty_queue,responses,updates,queue_control,completion}};
    const std::array<void*,7> output={{owners,registry,dirty_queue,responses,updates,queue_control,completion}};unsigned state_uploads=0;
    for(unsigned i=0;i<9;++i){auto uploaded=ctx.upload(die,i,input[i],sizes[i]);if(i==2||i==3||i==4||i==7)state_uploads+=uploaded;}
    auto run=(*d.owner)(b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7],b[8],slots,lanes,die,dies,session,command_capacity,response_capacity,update_capacity,dirty_capacity,command_read,command_write,response_read,response_write,update_read,update_write,max_commands,max_updates,max_visits,subscriber_filter);
    if(run.wait()!=ERT_CMD_STATE_COMPLETED)throw std::runtime_error("publisher CU did not complete");
    for(unsigned i=2;i<9;++i)ctx.download(die,i,output[i-2],sizes[i]);
    std::lock_guard<std::mutex> log_lock(ctx.log_mutex);
    std::cerr<<"XRT publisher die="<<die<<" session="<<session<<" commands="<<completion->w[3]<<" updates="<<completion->w[4]<<" visits="<<completion->w[5]<<" error="<<completion->w[6]<<" state_uploads="<<state_uploads<<'\n';
}
extern "C" void dieroute_summary_hbm(
    const SummaryWord* commands,const std::uint64_t* topology,
    SummaryWord* owners,SummaryWord* shadows,SummaryWord* responses,SummaryWord* completion,
    std::uint32_t slots,std::uint32_t lanes,std::uint32_t die,std::uint32_t dies,
    std::uint64_t session,std::uint32_t command_capacity,std::uint32_t response_capacity,
    std::uint64_t command_read,std::uint64_t command_write,
    std::uint64_t response_read,std::uint64_t response_write,std::uint32_t max_steps){
    limits(slots,lanes,die,command_capacity,response_capacity);auto& ctx=context();auto& d=ctx.dies[die];auto& b=d.buffers;
    const std::array<unsigned,6> buffers={{9,1,2,10,11,12}};const std::array<std::size_t,6> sizes={{command_capacity*128,slots*8,slots*64,slots*lanes*64,response_capacity*128,64}};
    const std::array<const void*,6> input={{commands,topology,owners,shadows,responses,completion}};const std::array<void*,4> output={{owners,shadows,responses,completion}};unsigned state_uploads=0;
    for(unsigned i=0;i<6;++i){auto uploaded=ctx.upload(die,buffers[i],input[i],sizes[i]);if(i==2||i==3)state_uploads+=uploaded;}
    auto run=(*d.receiver)(b[9],b[1],b[2],b[10],b[11],b[12],slots,lanes,die,dies,session,command_capacity,response_capacity,command_read,command_write,response_read,response_write,max_steps);
    if(run.wait()!=ERT_CMD_STATE_COMPLETED)throw std::runtime_error("receiver CU did not complete");
    for(unsigned i=2;i<6;++i)ctx.download(die,buffers[i],output[i-2],sizes[i]);
    std::lock_guard<std::mutex> log_lock(ctx.log_mutex);
    std::cerr<<"XRT receiver die="<<die<<" session="<<session<<" commands="<<completion->w[2]<<" error="<<completion->w[3]<<" state_uploads="<<state_uploads<<'\n';
}
}
