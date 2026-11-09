#include "native_search_hbm_summary_binding.hpp"
extern "C" void dieroute_native_search_summary_binding_hbm(
 const std::uint64_t* packet,dieroute::NativeSearchResourceObservation* journal,std::uint64_t* metadata,
 std::uint32_t capacity,std::uint32_t node,std::uint32_t owner,std::uint32_t worker,std::uint32_t membership,
 std::uint64_t serial,std::uint64_t session,std::uint64_t epoch,std::uint32_t own,std::uint64_t present){
#pragma HLS INTERFACE m_axi port=packet offset=slave bundle=observations depth=8
#pragma HLS INTERFACE m_axi port=journal offset=slave bundle=observations depth=1024
#pragma HLS INTERFACE m_axi port=metadata offset=slave bundle=metadata_memory depth=8
#pragma HLS INTERFACE s_axilite port=packet bundle=control
#pragma HLS INTERFACE s_axilite port=journal bundle=control
#pragma HLS INTERFACE s_axilite port=metadata bundle=control
#pragma HLS INTERFACE s_axilite port=capacity bundle=control
#pragma HLS INTERFACE s_axilite port=node bundle=control
#pragma HLS INTERFACE s_axilite port=owner bundle=control
#pragma HLS INTERFACE s_axilite port=worker bundle=control
#pragma HLS INTERFACE s_axilite port=membership bundle=control
#pragma HLS INTERFACE s_axilite port=serial bundle=control
#pragma HLS INTERFACE s_axilite port=session bundle=control
#pragma HLS INTERFACE s_axilite port=epoch bundle=control
#pragma HLS INTERFACE s_axilite port=own bundle=control
#pragma HLS INTERFACE s_axilite port=present bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
 if(metadata[0]>UINT32_MAX||own>1){metadata[1]=std::uint64_t(dieroute::NativeSearchObservationStatus::invalid);return;}
 auto used=std::uint32_t(metadata[0]);auto cost=metadata[2];
 auto result=dieroute::native_search_observe_summary<1024>(packet,node,owner,worker,membership,serial,session,epoch,journal,capacity,used,own!=0,present,cost);
 metadata[0]=used;metadata[1]=std::uint64_t(result);
 if(result==dieroute::NativeSearchObservationStatus::ok)metadata[2]=cost;
}
