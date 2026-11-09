#include "native_search_hbm_csr.hpp"
extern "C" void dieroute_native_search_csr_hbm(const std::uint64_t* offsets,const std::uint64_t* arcs,const std::uint64_t* policy,std::uint64_t* metadata,std::uint64_t* output,std::uint32_t nodes,std::uint64_t arc_count,std::uint32_t dies,std::uint32_t source,std::uint32_t net,std::uint64_t max_visits){
#pragma HLS INTERFACE m_axi port=offsets offset=slave bundle=graph_memory depth=1025
#pragma HLS INTERFACE m_axi port=arcs offset=slave bundle=graph_memory depth=1024
#pragma HLS INTERFACE m_axi port=policy offset=slave bundle=graph_memory depth=1024
#pragma HLS INTERFACE m_axi port=metadata offset=slave bundle=commands depth=8
#pragma HLS INTERFACE m_axi port=output offset=slave bundle=commands depth=8
#pragma HLS INTERFACE s_axilite port=offsets bundle=control
#pragma HLS INTERFACE s_axilite port=arcs bundle=control
#pragma HLS INTERFACE s_axilite port=policy bundle=control
#pragma HLS INTERFACE s_axilite port=metadata bundle=control
#pragma HLS INTERFACE s_axilite port=output bundle=control
#pragma HLS INTERFACE s_axilite port=nodes bundle=control
#pragma HLS INTERFACE s_axilite port=arc_count bundle=control
#pragma HLS INTERFACE s_axilite port=dies bundle=control
#pragma HLS INTERFACE s_axilite port=source bundle=control
#pragma HLS INTERFACE s_axilite port=net bundle=control
#pragma HLS INTERFACE s_axilite port=max_visits bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
 auto cursor=metadata[0],visited=metadata[1];dieroute::NativeCSRArc value{};
 auto result=dieroute::native_search_next_arc<134217728,536870912>(offsets,arcs,policy,nodes,arc_count,dies,source,net,max_visits,cursor,visited,value);
 if(result!=dieroute::NativeCSRStatus::invalid){metadata[0]=cursor;metadata[1]=visited;}
 metadata[2]=std::uint64_t(result);
 if(result==dieroute::NativeCSRStatus::arc){output[0]=value.node;output[1]=value.edge;output[2]=value.owner;output[3]=value.membership;}
}
