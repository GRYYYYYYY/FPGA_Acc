#include "native_search_hbm_frontier.hpp"
extern "C" void dieroute_native_search_frontier_hbm(
 dieroute::NativeSearchLabelSlot* labels,dieroute::NativeSearchQueueEntry* queue,
 dieroute::NativeSearchLabelSlot* output,std::uint32_t* count,std::uint32_t* status,
 std::uint32_t label_capacity,std::uint32_t queue_capacity,std::uint64_t epoch){
#pragma HLS INTERFACE m_axi port=labels offset=slave bundle=labels_memory depth=1024
#pragma HLS INTERFACE m_axi port=queue offset=slave bundle=queue_memory depth=1024
#pragma HLS INTERFACE m_axi port=output offset=slave bundle=labels_memory depth=1
#pragma HLS INTERFACE m_axi port=count offset=slave bundle=metadata depth=1
#pragma HLS INTERFACE m_axi port=status offset=slave bundle=metadata depth=1
#pragma HLS INTERFACE s_axilite port=labels bundle=control
#pragma HLS INTERFACE s_axilite port=queue bundle=control
#pragma HLS INTERFACE s_axilite port=output bundle=control
#pragma HLS INTERFACE s_axilite port=count bundle=control
#pragma HLS INTERFACE s_axilite port=status bundle=control
#pragma HLS INTERFACE s_axilite port=label_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=queue_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=epoch bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
 auto used=*count;dieroute::NativeSearchLabelSlot value{};
 auto result=dieroute::native_search_take_frontier<1024>(labels,label_capacity,queue,queue_capacity,used,epoch,value);
 if(result==dieroute::NativeFrontierStatus::current)*output=value;
 if(result==dieroute::NativeFrontierStatus::current||result==dieroute::NativeFrontierStatus::skipped)*count=used;
 *status=std::uint32_t(result);
}
