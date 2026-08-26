#include "multi_pe.hpp"
#include "multiqueue.hpp"
namespace persistroute {
extern "C" void multi_pe_schedule(const Task tasks[MAX_TASKS],PEAssignment assignments[MAX_TASKS],std::uint32_t task_count,std::uint32_t pe_count,std::uint32_t bank_count,SchedulerMetrics* metrics){
#ifdef __SYNTHESIS__
#pragma HLS INTERFACE m_axi port=tasks bundle=gmem0
#pragma HLS INTERFACE m_axi port=assignments bundle=gmem1
#pragma HLS INTERFACE m_axi port=metrics bundle=gmem2
#pragma HLS INTERFACE s_axilite port=task_count bundle=control
#pragma HLS INTERFACE s_axilite port=pe_count bundle=control
#pragma HLS INTERFACE s_axilite port=bank_count bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
#endif
 SchedulerMetrics out{};if(task_count>MAX_TASKS||pe_count==0||pe_count>MQ_MAX_PE||bank_count==0||bank_count>HBM_BANKS){out.rejected=task_count;*metrics=out;return;}
 for(std::uint32_t i=0;i<task_count;++i){std::uint32_t pe=0;for(std::uint32_t p=1;p<pe_count;++p)if(out.pe_load[p]<out.pe_load[pe])pe=p;const std::uint32_t bank=(tasks[i].source^(tasks[i].sink>>4))%bank_count;assignments[i]={static_cast<std::uint16_t>(pe),static_cast<std::uint16_t>(bank),i,1,0};++out.pe_load[pe];++out.bank_load[bank];++out.assigned;}*metrics=out;
}
}
