#include "native_search_hbm_resource.hpp"
#include "native_search_hbm_labels.hpp"
#include "native_search_hbm_queue.hpp"
#include "xrt_device_context.hpp"
#include <xrt/xrt_kernel.h>
#include <xrt/xrt_bo.h>
#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>
namespace dieroute {
xrt::bo& native_commit_shared_bo(unsigned);
bool native_commit_source_matches(unsigned,const void*,std::size_t);
namespace {
void require(bool yes,const char* message){if(!yes)throw std::runtime_error(message);}
struct SearchDevice {
 xrt_host::DeviceContext& platform=xrt_host::device_context("DIEROUTE_NET_COMMIT_XCLBIN");
 xrt::kernel worker{platform.device,platform.uuid,"dieroute_native_search_worker_hbm:{search_worker}",xrt::kernel::cu_access_mode::exclusive};
 xrt::kernel reader{platform.device,platform.uuid,"dieroute_native_search_resource_hbm:{resource_reader}",xrt::kernel::cu_access_mode::exclusive};
 std::array<xrt::bo,7> bo;std::array<std::vector<unsigned char>,3> state;std::array<std::uint64_t,8> counters{};xrt::bo status;
 std::uint64_t worker_calls=0,reader_calls=0;bool initialized=false;
 SearchDevice(){const std::array<unsigned,7> args{0,1,2,3,4,5,17};for(unsigned i=0;i<7;++i){auto bytes=i<3?1024*64:64;bo[i]=xrt::bo(platform.device,bytes,worker.group_id(args[i]));std::vector<unsigned char> zero(bytes,0);bo[i].write(zero.data());bo[i].sync(XCL_BO_SYNC_BO_TO_DEVICE);if(i<3)state[i]=zero;}status=xrt::bo(platform.device,64,reader.group_id(4));std::array<std::uint64_t,8> zero{};status.write(zero.data());status.sync(XCL_BO_SYNC_BO_TO_DEVICE);
  require(reader.group_id(0)==int(native_commit_shared_bo(1).get_memory_group()),"policy group mismatch");require(reader.group_id(1)==int(native_commit_shared_bo(8).get_memory_group())&&reader.group_id(2)==int(native_commit_shared_bo(11).get_memory_group()),"authority group mismatch");require(reader.group_id(3)==worker.group_id(4),"observation group mismatch");
 }
 void state_input(unsigned i,const void* p){if(!initialized){bo[i].write(p,state[i].size(),0);bo[i].sync(XCL_BO_SYNC_BO_TO_DEVICE);std::memcpy(state[i].data(),p,state[i].size());}else require(!std::memcmp(p,state[i].data(),state[i].size()),"CPU changed worker authority");}
};
SearchDevice& context(){static SearchDevice d;return d;}
}
extern "C" void dieroute_native_search_resource_hbm(const std::uint64_t* policy,const SummaryWord* resources,const std::uint64_t* control_words,std::uint64_t* output_words,std::uint32_t* result,std::uint32_t nodes,std::uint32_t dies,std::uint32_t shard_capacity,std::uint32_t tree_capacity,std::uint32_t node,std::uint64_t session,std::uint64_t revision,std::uint64_t epoch){
 auto& d=context();require(native_commit_source_matches(1,policy,nodes*8)&&native_commit_source_matches(8,resources,dies*shard_capacity*64)&&native_commit_source_matches(11,control_words,64),"authority input differs from device snapshot");
 auto run=d.reader(native_commit_shared_bo(1),native_commit_shared_bo(8),native_commit_shared_bo(11),d.bo[4],d.status,nodes,dies,shard_capacity,tree_capacity,node,session,revision,epoch);require(run.wait()==ERT_CMD_STATE_COMPLETED,"resource CU did not complete");d.bo[4].sync(XCL_BO_SYNC_BO_FROM_DEVICE);d.bo[4].read(output_words,64,0);d.status.sync(XCL_BO_SYNC_BO_FROM_DEVICE);d.status.read(result,4,0);++d.reader_calls;std::cerr<<"XRT resource call="<<d.reader_calls<<" node="<<node<<" status="<<*result<<" occupancy="<<output_words[2]<<" history="<<output_words[3]<<" version="<<output_words[1]<<'\n';
}
extern "C" void dieroute_native_search_worker_hbm(NativeSearchLabelSlot* labels,NativeSearchQueueEntry* queue,NativeSearchResourceObservation* journal,const NativeSearchLabelSlot* parent,const std::uint64_t* observation_words,std::uint64_t* metadata,std::uint32_t label_capacity,std::uint32_t queue_capacity,std::uint32_t journal_capacity,std::uint32_t dst,std::uint32_t edge,std::uint64_t session,std::uint32_t own,std::uint64_t present,std::uint64_t potential,std::uint64_t max_cost,std::uint32_t credit,NativeSearchLabelSlot* output,std::uint32_t operation){
 auto& d=context();require(label_capacity<=1024&&queue_capacity<=1024&&journal_capacity<=1024,"worker fixture capacities");d.state_input(0,labels);d.state_input(1,queue);d.state_input(2,journal);require(metadata[0]==d.counters[0]&&metadata[1]==d.counters[1],"CPU changed worker counters");
 xrt::bo* parent_bo=&d.bo[3];
 if(operation==1){NativeSearchLabelSlot last{};d.bo[6].sync(XCL_BO_SYNC_BO_FROM_DEVICE);d.bo[6].read(&last,64,0);require(!std::memcmp(&last,parent,64),"relaxation parent not produced by frontier CU");parent_bo=&d.bo[6];std::array<std::uint64_t,8> value{};d.bo[4].sync(XCL_BO_SYNC_BO_FROM_DEVICE);d.bo[4].read(value.data(),64,0);require(!std::memcmp(value.data(),observation_words,64),"observation not produced by resource CU");}
 else{d.bo[3].write(parent,64,0);d.bo[3].sync(XCL_BO_SYNC_BO_TO_DEVICE);}
 auto run=d.worker(d.bo[0],d.bo[1],d.bo[2],*parent_bo,d.bo[4],d.bo[5],label_capacity,queue_capacity,journal_capacity,dst,edge,session,own,present,potential,max_cost,credit,d.bo[6],operation);require(run.wait()==ERT_CMD_STATE_COMPLETED,"worker CU did not complete");d.initialized=true;
 const std::array<void*,3> outputs{labels,queue,journal};for(unsigned i=0;i<3;++i){d.bo[i].sync(XCL_BO_SYNC_BO_FROM_DEVICE);d.bo[i].read(outputs[i],d.state[i].size(),0);std::memcpy(d.state[i].data(),outputs[i],d.state[i].size());}d.bo[5].sync(XCL_BO_SYNC_BO_FROM_DEVICE);d.bo[5].read(metadata,64,0);std::memcpy(d.counters.data(),metadata,64);d.bo[6].sync(XCL_BO_SYNC_BO_FROM_DEVICE);d.bo[6].read(output,64,0);++d.worker_calls;std::cerr<<"XRT resource_worker call="<<d.worker_calls<<" op="<<operation<<" queued="<<metadata[0]<<" observations="<<metadata[1]<<" status="<<metadata[2]<<" authority_uploads=0\n";
}
}
namespace dieroute {
std::uint64_t native_commit_call_count();
std::uint64_t native_commit_upload_count();
SummaryWord native_resource_joint_metrics(){auto& d=context();SummaryWord result{};result.w[0]=native_commit_call_count();result.w[1]=d.reader_calls;result.w[2]=d.worker_calls;result.w[3]=native_commit_upload_count();return result;}
}
