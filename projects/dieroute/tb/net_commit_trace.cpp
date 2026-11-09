// Test-only linker wrapper. Record the actual kernel ABI, without modifying
// either the production kernel or the C/RTL testbench.
#include "net_commit_hbm.hpp"
#include <cstdlib>
#include <fstream>
#include <stdexcept>
#define COMMIT_PARAMETERS \
 const dieroute::SummaryWord* command,const std::uint64_t* policy,const std::uint64_t* offsets,const std::uint64_t* arcs, \
 const std::uint64_t* reads,const dieroute::SummaryWord* shadows,const dieroute::SummaryWord* branches,const std::uint64_t* paths, \
 dieroute::SummaryWord* resources,dieroute::SummaryWord* trees,dieroute::SummaryWord* nets,dieroute::SummaryWord* control,dieroute::SummaryWord* scratch, \
 dieroute::SummaryWord* deltas,dieroute::SummaryWord* completion, \
 std::uint32_t node_count,std::uint64_t arc_count,std::uint32_t dies,std::uint32_t shard_capacity, \
 std::uint32_t net_capacity,std::uint32_t tree_capacity,std::uint32_t read_capacity,std::uint32_t shadow_capacity, \
 std::uint32_t branch_capacity,std::uint32_t path_capacity,std::uint32_t scratch_capacity,std::uint32_t delta_capacity
#define COMMIT_ARGUMENTS command,policy,offsets,arcs,reads,shadows,branches,paths,resources,trees,nets,control,scratch,deltas,completion,node_count,arc_count,dies,shard_capacity,net_capacity,tree_capacity,read_capacity,shadow_capacity,branch_capacity,path_capacity,scratch_capacity,delta_capacity
extern "C" void __real_dieroute_net_commit_hbm(COMMIT_PARAMETERS);
extern "C" void __wrap_dieroute_net_commit_hbm(COMMIT_PARAMETERS){
 const char* path=std::getenv("DIEROUTE_NET_COMMIT_TRACE");
 if(!path){__real_dieroute_net_commit_hbm(COMMIT_ARGUMENTS);return;}
 static std::ofstream out(path,std::ios::binary|std::ios::trunc);static std::uint64_t sequence=0;
 if(!out)throw std::runtime_error("cannot write net commit trace");
 auto write=[&](const void* p,std::uint64_t bytes){out.write(static_cast<const char*>(p),bytes);};
 std::uint64_t state_bytes=(std::uint64_t(dies)*shard_capacity+tree_capacity+net_capacity+1)*64;
 std::uint64_t input_bytes=(std::uint64_t(node_count)*2+1+arc_count)*8+128+std::uint64_t(read_capacity)*16+std::uint64_t(shadow_capacity+branch_capacity)*64+std::uint64_t(path_capacity)*16;
 std::uint64_t header[16]={UINT64_C(0x3130544d434e5244),128+input_bytes+state_bytes*2+64+std::uint64_t(delta_capacity)*64,sequence++,node_count,arc_count,dies,shard_capacity,net_capacity,tree_capacity,read_capacity,shadow_capacity,branch_capacity,path_capacity,scratch_capacity,delta_capacity,0};
 write(header,sizeof(header));write(policy,std::uint64_t(node_count)*8);write(offsets,(std::uint64_t(node_count)+1)*8);write(arcs,arc_count*8);write(command,128);write(reads,std::uint64_t(read_capacity)*16);write(shadows,std::uint64_t(shadow_capacity)*64);write(branches,std::uint64_t(branch_capacity)*64);write(paths,std::uint64_t(path_capacity)*16);
 auto state=[&]{write(resources,std::uint64_t(dies)*shard_capacity*64);write(trees,std::uint64_t(tree_capacity)*64);write(nets,std::uint64_t(net_capacity)*64);write(control,64);};
 state();__real_dieroute_net_commit_hbm(COMMIT_ARGUMENTS);state();write(completion,64);write(deltas,std::uint64_t(delta_capacity)*64);
 if(!out)throw std::runtime_error("net commit trace write failed");
}
