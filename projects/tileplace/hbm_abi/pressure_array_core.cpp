#include "pressure_array_core.hpp"
namespace tileplace_hbm {
extern "C" void tileplace_pressure_array(const PrefixLine* lines,const PrefixEntry* entries,
 const PressureQuery* queries,PressureResult* outputs,std::uint64_t line_count,
 std::uint64_t entry_count,std::uint32_t query_count) {
#ifdef __SYNTHESIS__
#pragma HLS INTERFACE m_axi port=lines bundle=prefix_lines
#pragma HLS INTERFACE m_axi port=entries bundle=prefix_entries
#pragma HLS INTERFACE m_axi port=queries bundle=query_input
#pragma HLS INTERFACE m_axi port=outputs bundle=query_output
#pragma HLS INTERFACE s_axilite port=line_count bundle=control
#pragma HLS INTERFACE s_axilite port=entry_count bundle=control
#pragma HLS INTERFACE s_axilite port=query_count bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
#endif
 for(std::uint32_t i=0;i<query_count;++i)outputs[i]=pressure_array_query(lines,line_count,entries,entry_count,queries[i]);
}
}
