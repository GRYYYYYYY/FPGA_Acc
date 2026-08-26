#include "fusionpar.hpp"
namespace fusionpar {
extern "C" void fusionpar_kernel(Move moves[MAX_MOVES],const AffectedConnection affected[MAX_AFFECTED],Resource resources[MAX_RESOURCES],MoveResult results[MAX_MOVES],std::uint32_t move_count,std::uint32_t affected_total,std::uint32_t resource_count,std::uint16_t sketch_reject_q,std::uint16_t detour_repair_q,Metrics* metrics){
#ifdef __SYNTHESIS__
#pragma HLS INTERFACE m_axi port=moves bundle=gmem0
#pragma HLS INTERFACE m_axi port=affected bundle=gmem1
#pragma HLS INTERFACE m_axi port=resources bundle=gmem2
#pragma HLS INTERFACE m_axi port=results bundle=gmem3
#pragma HLS INTERFACE s_axilite port=move_count bundle=control
#pragma HLS INTERFACE s_axilite port=affected_total bundle=control
#pragma HLS INTERFACE s_axilite port=resource_count bundle=control
#pragma HLS INTERFACE s_axilite port=sketch_reject_q bundle=control
#pragma HLS INTERFACE s_axilite port=detour_repair_q bundle=control
#pragma HLS INTERFACE m_axi port=metrics bundle=gmem4
#pragma HLS INTERFACE s_axilite port=return bundle=control
#endif
 Metrics out{};if(move_count>MAX_MOVES||affected_total>MAX_AFFECTED||resource_count>MAX_RESOURCES){*metrics=out;return;}
 for(std::uint32_t i=0;i<move_count;++i){const Move m=moves[i];MoveResult r{0,0,m.place_version,0xffffffffU};if(m.predicted_overflow_q>sketch_reject_q){r.status=2;++out.rejected;results[i]=r;continue;}bool valid=true,repair=false;
  for(std::uint32_t j=0;j<m.affected_count;++j){
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE II=1
#endif
   const std::uint32_t idx=m.affected_begin+j;if(idx>=affected_total){valid=false;break;}const AffectedConnection a=affected[idx];if(a.resource_id>=resource_count||resources[a.resource_id].version!=a.resource_version){valid=false;r.conflict_connection=a.connection_id;break;}const int next=static_cast<int>(resources[a.resource_id].occupancy)+a.occupancy_delta;if(next<0||next>resources[a.resource_id].capacity){valid=false;r.conflict_connection=a.connection_id;break;}if(a.detour_q>detour_repair_q)repair=true;}
  if(!valid){r.status=3;++out.conflicts;if(m.repair_budget){r.repair_action=1;++out.repair_tasks;}results[i]=r;continue;}
  for(std::uint32_t j=0;j<m.affected_count;++j){const AffectedConnection a=affected[m.affected_begin+j];Resource& s=resources[a.resource_id];s.occupancy=static_cast<std::uint16_t>(static_cast<int>(s.occupancy)+a.occupancy_delta);++s.version;}
  ++moves[i].place_version;r.new_place_version=moves[i].place_version;r.status=1;if(repair&&m.repair_budget){r.repair_action=2;++out.repair_tasks;}++out.committed;out.reused_state_bytes+=static_cast<std::uint64_t>(m.affected_count)*sizeof(AffectedConnection);results[i]=r;}
 *metrics=out;
}
}
