#include "native_search_hbm_admission.hpp"
extern "C" void dieroute_native_search_admission_hbm(
 dieroute::NativeSearchLabelSlot* labels,dieroute::NativeSearchQueueEntry* queue,
 const dieroute::NativeSearchRelaxation* request,std::uint32_t* count,std::uint32_t* status,
 std::uint32_t label_capacity,std::uint32_t queue_capacity,std::uint32_t credit){
#pragma HLS INTERFACE m_axi port=labels offset=slave bundle=labels_memory depth=1024
#pragma HLS INTERFACE m_axi port=queue offset=slave bundle=queue_memory depth=1024
#pragma HLS INTERFACE m_axi port=request offset=slave bundle=commands depth=1
#pragma HLS INTERFACE m_axi port=count offset=slave bundle=metadata depth=1
#pragma HLS INTERFACE m_axi port=status offset=slave bundle=metadata depth=1
#pragma HLS INTERFACE s_axilite port=labels bundle=control
#pragma HLS INTERFACE s_axilite port=queue bundle=control
#pragma HLS INTERFACE s_axilite port=request bundle=control
#pragma HLS INTERFACE s_axilite port=count bundle=control
#pragma HLS INTERFACE s_axilite port=status bundle=control
#pragma HLS INTERFACE s_axilite port=label_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=queue_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=credit bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
 if(credit>1){*status=std::uint32_t(dieroute::NativeSearchAdmission::invalid);return;}
 auto used=*count;
 auto result=dieroute::native_search_admit<1024>(labels,label_capacity,queue,queue_capacity,used,*request,credit!=0);
 if(result==dieroute::NativeSearchAdmission::accepted)*count=used;
 *status=std::uint32_t(result);
}
