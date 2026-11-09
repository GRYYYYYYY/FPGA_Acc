#include "native_search_hbm_resource_sharded.hpp"
extern "C" void dieroute_native_search_resource_sharded_hbm(const std::uint64_t* policy,
 const dieroute::SummaryWord* resources0,const dieroute::SummaryWord* resources1,
 const dieroute::SummaryWord* resources2,const std::uint64_t* control_words,
 const std::uint64_t* configuration,std::uint64_t* result_words,std::uint64_t* observation_words){
#pragma HLS INTERFACE m_axi port=policy offset=slave bundle=graph_memory depth=12
#pragma HLS INTERFACE m_axi port=resources0 offset=slave bundle=owner0 depth=16
#pragma HLS INTERFACE m_axi port=resources1 offset=slave bundle=owner1 depth=16
#pragma HLS INTERFACE m_axi port=resources2 offset=slave bundle=owner2 depth=16
#pragma HLS INTERFACE m_axi port=control_words offset=slave bundle=authority_memory depth=8
#pragma HLS INTERFACE m_axi port=configuration offset=slave bundle=traffic_memory depth=8
#pragma HLS INTERFACE m_axi port=result_words offset=slave bundle=traffic_memory depth=8
#pragma HLS INTERFACE m_axi port=observation_words offset=slave bundle=traffic_memory depth=8
#pragma HLS AGGREGATE variable=resources0 compact=none
#pragma HLS AGGREGATE variable=resources1 compact=none
#pragma HLS AGGREGATE variable=resources2 compact=none
#pragma HLS INTERFACE s_axilite port=policy bundle=control
#pragma HLS INTERFACE s_axilite port=resources0 bundle=control
#pragma HLS INTERFACE s_axilite port=resources1 bundle=control
#pragma HLS INTERFACE s_axilite port=resources2 bundle=control
#pragma HLS INTERFACE s_axilite port=control_words bundle=control
#pragma HLS INTERFACE s_axilite port=configuration bundle=control
#pragma HLS INTERFACE s_axilite port=result_words bundle=control
#pragma HLS INTERFACE s_axilite port=observation_words bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
 for(unsigned i=0;i<5;++i)if(configuration[i]>UINT32_MAX){result_words[0]=std::uint64_t(dieroute::NativeResourceReadStatus::invalid);return;}
 dieroute::SummaryWord control{};for(unsigned i=0;i<8;++i)control.w[i]=control_words[i];
 dieroute::NativeSearchResourceObservation observation{};
 auto status=dieroute::native_search_read_resource_sharded<2097152>(policy,resources0,resources1,resources2,control,configuration[0],configuration[1],configuration[2],configuration[3],configuration[4],configuration[5],configuration[6],configuration[7],observation);
 result_words[0]=std::uint64_t(status);
 if(status!=dieroute::NativeResourceReadStatus::invalid){observation_words[0]=observation.node;observation_words[1]=observation.version;observation_words[2]=observation.occupancy;observation_words[3]=observation.history;observation_words[4]=observation.session;observation_words[5]=observation.epoch;observation_words[6]=observation.owner;observation_words[7]=observation.reserved;}
}
