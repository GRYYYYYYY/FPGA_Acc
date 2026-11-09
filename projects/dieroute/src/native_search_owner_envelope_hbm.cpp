#include "native_search_hbm_summary_envelope.hpp"
extern "C" void dieroute_native_search_owner_envelope_hbm(const std::uint64_t* packet,const std::uint64_t* envelope,std::uint64_t* output_words,std::uint32_t* status,std::uint32_t node,std::uint32_t owner,std::uint32_t worker,std::uint32_t membership,std::uint64_t serial,std::uint64_t session,std::uint64_t epoch,std::uint32_t operation,std::uint64_t ticket,std::uint32_t lane,std::uint32_t slot,std::uint32_t kind){
#pragma HLS INTERFACE m_axi port=packet offset=slave bundle=traffic_memory depth=8
#pragma HLS INTERFACE m_axi port=envelope offset=slave bundle=traffic_memory depth=8
#pragma HLS INTERFACE m_axi port=output_words offset=slave bundle=observations depth=8
#pragma HLS INTERFACE m_axi port=status offset=slave bundle=traffic_memory depth=1
#pragma HLS INTERFACE s_axilite port=packet bundle=control
#pragma HLS INTERFACE s_axilite port=envelope bundle=control
#pragma HLS INTERFACE s_axilite port=output_words bundle=control
#pragma HLS INTERFACE s_axilite port=status bundle=control
#pragma HLS INTERFACE s_axilite port=node bundle=control
#pragma HLS INTERFACE s_axilite port=owner bundle=control
#pragma HLS INTERFACE s_axilite port=worker bundle=control
#pragma HLS INTERFACE s_axilite port=membership bundle=control
#pragma HLS INTERFACE s_axilite port=serial bundle=control
#pragma HLS INTERFACE s_axilite port=session bundle=control
#pragma HLS INTERFACE s_axilite port=epoch bundle=control
#pragma HLS INTERFACE s_axilite port=operation bundle=control
#pragma HLS INTERFACE s_axilite port=ticket bundle=control
#pragma HLS INTERFACE s_axilite port=lane bundle=control
#pragma HLS INTERFACE s_axilite port=slot bundle=control
#pragma HLS INTERFACE s_axilite port=kind bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
 dieroute::NativeSearchResourceObservation value{};
 auto result=dieroute::NativeSummaryBindingStatus::invalid;
 if(kind==1)result=dieroute::native_search_bind_owner_reply(packet,envelope,node,owner,worker,membership,serial,session,epoch,operation,ticket,lane,slot,value);
 if(kind==2)result=dieroute::native_search_bind_owner_update(packet,envelope,node,owner,worker,membership,ticket,session,epoch,lane,slot,value);
 if(result==dieroute::NativeSummaryBindingStatus::ok){output_words[0]=value.node;output_words[1]=value.version;output_words[2]=value.occupancy;output_words[3]=value.history;output_words[4]=value.session;output_words[5]=value.epoch;output_words[6]=value.owner;output_words[7]=value.reserved;}
 *status=std::uint32_t(result);
}
