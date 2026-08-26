#include "dieroute.hpp"
namespace dieroute {
extern "C" void dieroute_kernel(Boundary boundaries[MAX_BOUNDARIES],const CrossDieTask tasks[MAX_TASKS],Allocation allocations[MAX_TASKS],DieQueue queues[MAX_DIES],std::uint32_t boundary_count,std::uint32_t task_count,std::uint32_t die_count,Metrics* metrics){
#ifdef __SYNTHESIS__
#pragma HLS INTERFACE m_axi port=boundaries bundle=gmem0
#pragma HLS INTERFACE m_axi port=tasks bundle=gmem1
#pragma HLS INTERFACE m_axi port=allocations bundle=gmem2
#pragma HLS INTERFACE m_axi port=queues bundle=gmem3
#pragma HLS INTERFACE s_axilite port=boundary_count bundle=control
#pragma HLS INTERFACE s_axilite port=task_count bundle=control
#pragma HLS INTERFACE s_axilite port=die_count bundle=control
#pragma HLS INTERFACE m_axi port=metrics bundle=gmem4
#pragma HLS INTERFACE s_axilite port=return bundle=control
#endif
 Metrics out{};if(boundary_count>MAX_BOUNDARIES||task_count>MAX_TASKS||die_count>MAX_DIES){*metrics=out;return;}
 for(std::uint32_t d=0;d<die_count;++d)queues[d]={0,0,0,0};
 for(std::uint32_t i=0;i<task_count;++i){const CrossDieTask t=tasks[i];std::uint32_t best=0xffffffffU;std::uint64_t best_score=~std::uint64_t{0};
  for(std::uint32_t b=0;b<boundary_count;++b){
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE II=1
#endif
   const Boundary x=boundaries[b];if(x.src_die!=t.src_die||x.dst_die!=t.dst_die||x.reserved+t.demand>x.capacity)continue;const std::uint64_t scarce=static_cast<std::uint64_t>(x.reserved+t.demand)*65536U/x.capacity;const std::uint64_t timing=static_cast<std::uint64_t>(x.delay_q)*t.criticality_q/65535U;const std::uint64_t score=scarce+x.history_q+timing;if(score<best_score||(score==best_score&&b<best)){best=b;best_score=score;}}
  if(best==0xffffffffU){allocations[i]={0xffff,2,0,0xffffffffU};++out.rejected;continue;}Boundary& x=boundaries[best];allocations[i]={static_cast<std::uint16_t>(best),1,x.version,static_cast<std::uint32_t>(best_score)};x.reserved=static_cast<std::uint16_t>(x.reserved+t.demand);++x.version;++out.shadow_updates;++out.allocated;out.total_score_q+=best_score;
  const std::uint16_t target=queues[t.src_die].count<=queues[t.dst_die].count?t.src_die:t.dst_die;++queues[target].count;queues[target].total_demand+=t.demand;if(t.criticality_q>49151)++queues[target].critical_count;if(target!=t.src_die){++queues[target].migrations;++out.migrations;}}
 *metrics=out;
}
}
