// Dynamic native owner/receiver adapter. No CPU kernel is linked.
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
#include <algorithm>
#include <limits>
namespace dieroute {
namespace {
struct Device {
    xrt_host::DeviceContext& platform=xrt_host::device_context("DIEROUTE_OWNER_PUBLISH_XCLBIN");
    xrt::device& device=platform.device;xrt::uuid uuid=platform.uuid;
    std::mutex log_mutex;
    struct Die {std::unique_ptr<xrt::kernel> owner,receiver;std::array<xrt::bo,13> buffers;std::array<std::vector<unsigned char>,13> snapshots;unsigned slots=0,lanes=0,dirty_capacity=0;const void* topology=nullptr;};
    std::array<Die,3> dies;
    Device(){
        for(unsigned d=0;d<3;++d){auto& die=dies[d];
            die.owner=std::make_unique<xrt::kernel>(device,uuid,"dieroute_owner_publish_hbm:{owner_die"+std::to_string(d)+"}",xrt::kernel::cu_access_mode::exclusive);
            die.receiver=std::make_unique<xrt::kernel>(device,uuid,"dieroute_summary_hbm:{summary_die"+std::to_string(d)+"}",xrt::kernel::cu_access_mode::exclusive);
            for(unsigned arg:{1,2})if(die.owner->group_id(arg)!=die.receiver->group_id(arg))throw std::runtime_error("owner/receiver shared BO bank mismatch");
            if(die.owner->group_id(2)==die.owner->group_id(3)||die.owner->group_id(2)==die.receiver->group_id(3))throw std::runtime_error("owner/registry/cache bank alias");

        }
    }
    static std::size_t size(std::uint64_t count,std::uint64_t width){if(count>std::numeric_limits<std::size_t>::max()/width)throw std::runtime_error("native endpoint size overflow");return count*width;}
    void transfer(unsigned d,unsigned index,const void* source,void* target,std::size_t bytes,bool upload){
        if(bytes&&!(upload?source:target))throw std::runtime_error("null native endpoint transfer pointer");
        auto& b=dies[d].buffers[index];constexpr std::size_t chunk=16*1024*1024;
        for(std::size_t off=0;off<bytes;off+=chunk){auto n=std::min(chunk,bytes-off);if(upload){b.write(static_cast<const unsigned char*>(source)+off,n,off);b.sync(XCL_BO_SYNC_BO_TO_DEVICE,n,off);}else{b.sync(XCL_BO_SYNC_BO_FROM_DEVICE,n,off);b.read(static_cast<unsigned char*>(target)+off,n,off);}}
    }
    void ensure(unsigned d,unsigned index,std::size_t bytes){
        auto& die=dies[d];if(die.snapshots[index].size()>=bytes)return;
        unsigned arg=index<9?index:std::array<unsigned,4>{0,3,4,5}[index-9];auto group=index<9?die.owner->group_id(arg):die.receiver->group_id(arg);
        die.buffers[index]=xrt::bo{};die.buffers[index]=xrt::bo(device,bytes,group);die.snapshots[index].resize(bytes,0);transfer(d,index,die.snapshots[index].data(),nullptr,bytes,true);
    }
    void configure(unsigned d,unsigned slots,unsigned lanes,unsigned dirty,unsigned command,unsigned response,unsigned updates,const void* topology){
        auto& die=dies[d];if(die.slots){if(die.slots!=slots||die.lanes!=lanes||die.dirty_capacity!=dirty||die.topology!=topology)throw std::runtime_error("native endpoint immutable shape/topology pointer changed");}
        else{
            const std::array<std::size_t,13> sizes={size(command,128),size(slots,8),size(slots,64),size(slots,64),size(dirty,4),size(response,128),size(updates,128),64,64,size(command,128),size(std::uint64_t(slots)*lanes,64),size(response,128),64};
            for(unsigned i=0;i<13;++i)ensure(d,i,sizes[i]);
            transfer(d,1,topology,nullptr,sizes[1],true);std::memcpy(die.snapshots[1].data(),topology,sizes[1]);die.slots=slots;die.lanes=lanes;die.dirty_capacity=dirty;die.topology=topology;
            std::lock_guard<std::mutex> log_lock(log_mutex);std::cerr<<"XRT native endpoint configured die="<<d<<" slots="<<slots<<" lanes="<<lanes<<" dirty="<<dirty<<'\n';
        }
        ensure(d,0,size(command,128));ensure(d,5,size(response,128));ensure(d,6,size(updates,128));
    }
    unsigned upload(unsigned d,unsigned index,const void* p,std::size_t bytes){
        auto& die=dies[d];if(bytes>die.snapshots[index].size()||(!p&&bytes))throw std::runtime_error("native endpoint input bounds/pointer");if(!std::memcmp(p,die.snapshots[index].data(),bytes))return 0;
        if(index==1||index==2||index==3||index==4||index==7||index==10)throw std::runtime_error("host attempted to overwrite device endpoint state or topology");
        transfer(d,index,p,nullptr,bytes,true);std::memcpy(die.snapshots[index].data(),p,bytes);return 1;
    }
    void download(unsigned d,unsigned index,void* p,std::size_t bytes){if(bytes>dies[d].snapshots[index].size())throw std::runtime_error("native endpoint output bounds");transfer(d,index,nullptr,p,bytes,false);std::memcpy(dies[d].snapshots[index].data(),p,bytes);}

};
Device& context(){static Device d;return d;}
void limits(unsigned slots,unsigned lanes,unsigned die,unsigned command,unsigned response){if(!slots||slots>(1u<<24)||!lanes||lanes>8||die>=3||!command||command>(1u<<16)||!response||response>(1u<<16))throw std::runtime_error("native XRT endpoint dimensions");}
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
    limits(slots,lanes,die,command_capacity,response_capacity);if(!update_capacity||update_capacity>(1u<<16)||!dirty_capacity||dirty_capacity>(1u<<24))throw std::runtime_error("native publisher queue dimensions");auto& ctx=context();ctx.configure(die,slots,lanes,dirty_capacity,command_capacity,response_capacity,update_capacity,topology);auto& d=ctx.dies[die];auto& b=d.buffers;
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
    limits(slots,lanes,die,command_capacity,response_capacity);auto& ctx=context();auto& d=ctx.dies[die];if(!d.slots||d.slots!=slots||d.lanes!=lanes||d.topology!=topology)throw std::runtime_error("native receiver requires matching owner bootstrap");ctx.ensure(die,9,Device::size(command_capacity,128));ctx.ensure(die,11,Device::size(response_capacity,128));auto& b=d.buffers;
    const std::array<unsigned,6> buffers={{9,1,2,10,11,12}};const std::array<std::size_t,6> sizes={{command_capacity*128,slots*8,slots*64,Device::size(std::uint64_t(slots)*lanes,64),response_capacity*128,64}};
    const std::array<const void*,6> input={{commands,topology,owners,shadows,responses,completion}};const std::array<void*,4> output={{owners,shadows,responses,completion}};unsigned state_uploads=0;
    for(unsigned i=0;i<6;++i){auto uploaded=ctx.upload(die,buffers[i],input[i],sizes[i]);if(i==2||i==3)state_uploads+=uploaded;}
    auto run=(*d.receiver)(b[9],b[1],b[2],b[10],b[11],b[12],slots,lanes,die,dies,session,command_capacity,response_capacity,command_read,command_write,response_read,response_write,max_steps);
    if(run.wait()!=ERT_CMD_STATE_COMPLETED)throw std::runtime_error("receiver CU did not complete");
    for(unsigned i=2;i<6;++i)ctx.download(die,buffers[i],output[i-2],sizes[i]);
    std::lock_guard<std::mutex> log_lock(ctx.log_mutex);
    std::cerr<<"XRT receiver die="<<die<<" session="<<session<<" commands="<<completion->w[2]<<" error="<<completion->w[3]<<" state_uploads="<<state_uploads<<'\n';
}
}
