#include "native_search_hbm_observation.hpp"
extern "C" void dieroute_native_search_observation_hbm(
 const std::uint64_t* observation_words,dieroute::NativeSearchResourceObservation* journal,
 std::uint64_t* metadata,std::uint32_t capacity,std::uint64_t expected_node,
 std::uint64_t session,std::uint64_t epoch,std::uint32_t own,std::uint64_t present){
#pragma HLS INTERFACE m_axi port=observation_words offset=slave bundle=observations depth=8
#pragma HLS INTERFACE m_axi port=journal offset=slave bundle=observations depth=1024
#pragma HLS INTERFACE m_axi port=metadata offset=slave bundle=metadata_memory depth=8
#pragma HLS INTERFACE s_axilite port=observation_words bundle=control
#pragma HLS INTERFACE s_axilite port=journal bundle=control
#pragma HLS INTERFACE s_axilite port=metadata bundle=control
#pragma HLS INTERFACE s_axilite port=capacity bundle=control
#pragma HLS INTERFACE s_axilite port=expected_node bundle=control
#pragma HLS INTERFACE s_axilite port=session bundle=control
#pragma HLS INTERFACE s_axilite port=epoch bundle=control
#pragma HLS INTERFACE s_axilite port=own bundle=control
#pragma HLS INTERFACE s_axilite port=present bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
 // Metadata: used, status, cost. Rejection may update status only; overflow
 // retains the attempted observation and count, preserving previous cost.
 if(metadata[0]>UINT32_MAX||own>1){metadata[1]=std::uint64_t(dieroute::NativeSearchObservationStatus::invalid);return;}
 // Scalar input words avoid the Vitis 2022.2 struct wrapper temporary
 // losing alignment. Field order is the exact 64-byte observation ABI.
 const dieroute::NativeSearchResourceObservation value{observation_words[0],observation_words[1],observation_words[2],observation_words[3],observation_words[4],observation_words[5],observation_words[6],observation_words[7]};
 auto used=std::uint32_t(metadata[0]);auto cost=metadata[2];
 auto status=dieroute::native_search_observe_cost<1024>(value,expected_node,session,epoch,journal,capacity,used,own!=0,present,cost);
 if(status==dieroute::NativeSearchObservationStatus::ok||status==dieroute::NativeSearchObservationStatus::cost_overflow)metadata[0]=used;
 if(status==dieroute::NativeSearchObservationStatus::ok)metadata[2]=cost;
 metadata[1]=std::uint64_t(status);
}
