// Link this adapter with the *same* summary_hbm_tb.cpp used by HLS. The CPU
// implementation is deliberately absent: every call executes the loaded CU.
#include "summary_hbm.hpp"
#include <xrt/xrt_device.h>
#include <xrt/xrt_kernel.h>
#include <xrt/xrt_bo.h>
#include <array>
#include <memory>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <cstring>
#include <vector>
namespace dieroute {
struct SummaryDevice {
    xrt::device device{0};xrt::uuid uuid;
    std::array<std::unique_ptr<xrt::kernel>,3> kernels;
    std::array<std::array<xrt::bo,6>,3> buffers;
    std::array<std::array<std::vector<unsigned char>,6>,3> snapshots;
    SummaryDevice(){
        const char* path=std::getenv("DIEROUTE_SUMMARY_XCLBIN");if(!path)throw std::runtime_error("DIEROUTE_SUMMARY_XCLBIN required");uuid=device.load_xclbin(path);
        for(unsigned die=0;die<3;++die){auto name="dieroute_summary_hbm:{summary_die"+std::to_string(die)+"}";kernels[die]=std::make_unique<xrt::kernel>(device,uuid,name,xrt::kernel::cu_access_mode::exclusive);
            std::cerr<<"CU summary_die"<<die<<" argument groups:";for(unsigned arg=0;arg<6;++arg)std::cerr<<' '<<kernels[die]->group_id(arg);std::cerr<<'\n';
            if(kernels[die]->group_id(2)==kernels[die]->group_id(3))throw std::runtime_error("owner/cache bank alias");
            const std::array<std::size_t,6> capacity={{32*64,16*8,16*64,64*64,32*64,64}};
            for(unsigned i=0;i<6;++i){buffers[die][i]=xrt::bo(device,capacity[i],kernels[die]->group_id(i));snapshots[die][i].resize(capacity[i],0);buffers[die][i].write(snapshots[die][i].data());buffers[die][i].sync(XCL_BO_SYNC_BO_TO_DEVICE);}
        }
    }
};
extern "C" void dieroute_summary_hbm(
    const SummaryWord* commands,const std::uint64_t* topology,
    SummaryWord* owners,SummaryWord* shadows,SummaryWord* responses,SummaryWord* completion,
    std::uint32_t slots,std::uint32_t lanes,std::uint32_t die,std::uint32_t dies,
    std::uint64_t session,std::uint32_t command_capacity,std::uint32_t response_capacity,
    std::uint64_t command_read,std::uint64_t command_write,
    std::uint64_t response_read,std::uint64_t response_write,std::uint32_t max_steps){
    static SummaryDevice context;
    if(die>=3||!slots||slots>16||!lanes||lanes>4||!command_capacity||command_capacity>16||!response_capacity||response_capacity>16)throw std::runtime_error("XRT fixture allocation limits");
    auto& kernel=*context.kernels[die];
    const std::array<std::size_t,6> sizes={{command_capacity*2*sizeof(SummaryWord),slots*sizeof(std::uint64_t),slots*sizeof(SummaryWord),slots*lanes*sizeof(SummaryWord),response_capacity*2*sizeof(SummaryWord),sizeof(SummaryWord)}};
    const std::array<const void*,6> input={{commands,topology,owners,shadows,responses,completion}};
    const std::array<void*,4> output={{owners,shadows,responses,completion}};
    auto& buffers=context.buffers[die];auto& snapshots=context.snapshots[die];unsigned state_uploads=0;
    // Reuse BOs across calls. State already resident in HBM is not uploaded
    // again unless the fixture explicitly changes its host-side contents.
    for(unsigned i=0;i<6;++i)if(std::memcmp(snapshots[i].data(),input[i],sizes[i])){
        buffers[i].write(input[i],sizes[i],0);buffers[i].sync(XCL_BO_SYNC_BO_TO_DEVICE,sizes[i],0);std::memcpy(snapshots[i].data(),input[i],sizes[i]);state_uploads+=i==2||i==3;
    }
    auto run=kernel(buffers[0],buffers[1],buffers[2],buffers[3],buffers[4],buffers[5],slots,lanes,die,dies,session,command_capacity,response_capacity,command_read,command_write,response_read,response_write,max_steps);
    if(run.wait()!=ERT_CMD_STATE_COMPLETED)throw std::runtime_error("XRT kernel did not complete");
    for(unsigned i=2;i<6;++i){buffers[i].sync(XCL_BO_SYNC_BO_FROM_DEVICE);buffers[i].read(output[i-2],sizes[i],0);std::memcpy(snapshots[i].data(),output[i-2],sizes[i]);}
    std::cerr<<"XRT launch die="<<die<<" session="<<session<<" consumed="<<completion->w[2]<<" launch_error="<<completion->w[3]<<" writes="<<completion->w[4]<<" rejected="<<completion->w[5]<<" state_uploads="<<state_uploads<<'\n';
}
}
