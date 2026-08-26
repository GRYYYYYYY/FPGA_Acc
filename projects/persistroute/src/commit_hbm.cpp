#include "persistroute.hpp"
namespace persistroute {
extern "C" void commit_hbm_kernel(Resource* resources,const Task* tasks,const std::uint32_t* path_pool,
 const ReadEntry* read_pool,PathResult* results,std::uint32_t resource_count,std::uint32_t task_count,
 std::uint32_t transaction_capacity,std::uint32_t allow_overuse,Metrics* metrics){
#ifdef __SYNTHESIS__
#pragma HLS INTERFACE m_axi port=resources depth=8192 bundle=state
#pragma HLS INTERFACE m_axi port=tasks depth=1024 bundle=task
#pragma HLS INTERFACE m_axi port=path_pool depth=4096 bundle=path
#pragma HLS INTERFACE m_axi port=read_pool depth=4096 bundle=result
#pragma HLS INTERFACE m_axi port=results depth=1024 bundle=result
#pragma HLS INTERFACE m_axi port=metrics depth=1 bundle=result
#pragma HLS INTERFACE s_axilite port=resource_count bundle=control
#pragma HLS INTERFACE s_axilite port=task_count bundle=control
#pragma HLS INTERFACE s_axilite port=transaction_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=allow_overuse bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
#endif
 Metrics out{};
 for(std::uint32_t ti=0;ti<task_count;++ti){PathResult result=results[ti];if(result.status!=1)continue;bool valid=true;
  if(result.offset+result.length>transaction_capacity||result.read_offset+result.read_count>transaction_capacity)valid=false;
  for(std::uint32_t j=0;valid&&j<result.read_count;++j){
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE II=1
#endif
   const ReadEntry entry=read_pool[result.read_offset+j];if(entry.resource_id>=resource_count||
    (!allow_overuse&&resources[entry.resource_id].version!=entry.version&&
     resources[entry.resource_id].owner!=tasks[ti].net_id))valid=false;
  }
  for(std::uint32_t j=0;valid&&j<result.length;++j){const std::uint32_t id=path_pool[result.offset+j];if(id>=resource_count||(!allow_overuse&&resources[id].owner!=tasks[ti].net_id&&resources[id].occupancy>=resources[id].capacity))valid=false;}
  if(!valid){result.status=2;++out.conflicts;results[ti]=result;continue;}
  for(std::uint32_t j=0;j<result.length;++j){const std::uint32_t id=path_pool[result.offset+j];Resource state=resources[id];if(state.owner!=tasks[ti].net_id){const std::uint16_t prior=state.occupancy;if(state.occupancy!=65535U)++state.occupancy;++state.version;state.owner=prior==0?tasks[ti].net_id:0xffffffffU;resources[id]=state;}}
  result.status=4;++out.commits;results[ti]=result;
 }
 *metrics=out;
}
}
