#include "native_search_hbm_resource.hpp"
extern "C" void dieroute_native_search_resource_hbm(const std::uint64_t* policy,const dieroute::SummaryWord* resources,const std::uint64_t* control_words,std::uint64_t* output_words,std::uint32_t* status,std::uint32_t nodes,std::uint32_t dies,std::uint32_t shard_capacity,std::uint32_t tree_capacity,std::uint32_t node,std::uint64_t session,std::uint64_t revision,std::uint64_t epoch){
#pragma HLS INTERFACE m_axi port=policy offset=slave bundle=graph_memory depth=12
#pragma HLS INTERFACE m_axi port=resources offset=slave bundle=authority_memory depth=48
#pragma HLS INTERFACE m_axi port=control_words offset=slave bundle=authority_memory depth=8
#pragma HLS INTERFACE m_axi port=output_words offset=slave bundle=commands depth=8
#pragma HLS INTERFACE m_axi port=status offset=slave bundle=commands depth=1
#pragma HLS INTERFACE s_axilite port=policy bundle=control
#pragma HLS INTERFACE s_axilite port=resources bundle=control
#pragma HLS INTERFACE s_axilite port=control_words bundle=control
#pragma HLS INTERFACE s_axilite port=output_words bundle=control
#pragma HLS INTERFACE s_axilite port=status bundle=control
#pragma HLS INTERFACE s_axilite port=nodes bundle=control
#pragma HLS INTERFACE s_axilite port=dies bundle=control
#pragma HLS INTERFACE s_axilite port=shard_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=tree_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=node bundle=control
#pragma HLS INTERFACE s_axilite port=session bundle=control
#pragma HLS INTERFACE s_axilite port=revision bundle=control
#pragma HLS INTERFACE s_axilite port=epoch bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
 dieroute::SummaryWord control{};for(unsigned i=0;i<8;++i)control.w[i]=control_words[i];
 dieroute::NativeSearchResourceObservation output{};
 auto result=dieroute::native_search_read_resource<2097152>(policy,resources,control,nodes,dies,shard_capacity,tree_capacity,node,session,revision,epoch,output);
 if(result!=dieroute::NativeResourceReadStatus::invalid){output_words[0]=output.node;output_words[1]=output.version;output_words[2]=output.occupancy;output_words[3]=output.history;output_words[4]=output.session;output_words[5]=output.epoch;output_words[6]=output.owner;output_words[7]=output.reserved;}
 *status=std::uint32_t(result);
}
