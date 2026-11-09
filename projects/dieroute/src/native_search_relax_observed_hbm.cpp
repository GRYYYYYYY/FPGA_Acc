#include "native_search_hbm_relax_observed.hpp"
extern "C" void dieroute_native_search_relax_observed_hbm(dieroute::NativeSearchLabelSlot* labels,dieroute::NativeSearchQueueEntry* queue,dieroute::NativeSearchResourceObservation* journal,const dieroute::NativeSearchLabelSlot* parent,const std::uint64_t* observation_words,std::uint64_t* metadata,std::uint32_t label_capacity,std::uint32_t queue_capacity,std::uint32_t journal_capacity,std::uint32_t dst,std::uint32_t edge,std::uint64_t session,std::uint32_t own,std::uint64_t present,std::uint64_t potential,std::uint64_t max_cost,std::uint32_t credit){
#pragma HLS INTERFACE m_axi port=labels offset=slave bundle=search_memory depth=1024
#pragma HLS INTERFACE m_axi port=queue offset=slave bundle=search_memory depth=1024
#pragma HLS INTERFACE m_axi port=journal offset=slave bundle=traffic_memory depth=1024
#pragma HLS INTERFACE m_axi port=parent offset=slave bundle=search_memory depth=1
#pragma HLS INTERFACE m_axi port=observation_words offset=slave bundle=traffic_memory depth=8
#pragma HLS INTERFACE m_axi port=metadata offset=slave bundle=traffic_memory depth=8
#pragma HLS INTERFACE s_axilite port=labels bundle=control
#pragma HLS INTERFACE s_axilite port=queue bundle=control
#pragma HLS INTERFACE s_axilite port=journal bundle=control
#pragma HLS INTERFACE s_axilite port=parent bundle=control
#pragma HLS INTERFACE s_axilite port=observation_words bundle=control
#pragma HLS INTERFACE s_axilite port=metadata bundle=control
#pragma HLS INTERFACE s_axilite port=label_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=queue_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=journal_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=dst bundle=control
#pragma HLS INTERFACE s_axilite port=edge bundle=control
#pragma HLS INTERFACE s_axilite port=session bundle=control
#pragma HLS INTERFACE s_axilite port=own bundle=control
#pragma HLS INTERFACE s_axilite port=present bundle=control
#pragma HLS INTERFACE s_axilite port=potential bundle=control
#pragma HLS INTERFACE s_axilite port=max_cost bundle=control
#pragma HLS INTERFACE s_axilite port=credit bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
 // External capacities follow the native CPU diagnostic scale. AXI depth
 // pragmas size directed co-simulation buffers, not on-chip storage.
 if(label_capacity>2097152||queue_capacity>8388608||journal_capacity>33554432||metadata[0]>UINT32_MAX||metadata[1]>UINT32_MAX||own>1||credit>1){metadata[2]=std::uint64_t(dieroute::NativeObservedRelaxStatus::invalid);return;}
 const dieroute::NativeSearchResourceObservation value{observation_words[0],observation_words[1],observation_words[2],observation_words[3],observation_words[4],observation_words[5],observation_words[6],observation_words[7]};
 auto queued=std::uint32_t(metadata[0]),used=std::uint32_t(metadata[1]);
 auto result=dieroute::native_search_relax_observed<33554432>(labels,label_capacity,queue,queue_capacity,queued,*parent,dst,edge,value,session,journal,journal_capacity,used,own!=0,present,potential,max_cost,credit!=0);
 metadata[0]=queued;metadata[1]=used;metadata[2]=std::uint64_t(result);
}
