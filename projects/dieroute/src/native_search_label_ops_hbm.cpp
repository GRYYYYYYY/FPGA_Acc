#include "native_search_hbm_label_ops.hpp"
extern "C" void dieroute_native_search_label_ops_hbm(
 dieroute::NativeSearchLabelSlot* labels,const dieroute::NativeSearchQueueEntry* queue_item,
 dieroute::NativeSearchLabelSlot* output,std::uint32_t* status,
 std::uint32_t capacity,std::uint64_t epoch,std::uint32_t operation){
#pragma HLS INTERFACE m_axi port=labels offset=slave bundle=labels_memory depth=1024
#pragma HLS INTERFACE m_axi port=queue_item offset=slave bundle=commands depth=1
#pragma HLS INTERFACE m_axi port=output offset=slave bundle=commands depth=1
#pragma HLS INTERFACE m_axi port=status offset=slave bundle=metadata depth=1
#pragma HLS INTERFACE s_axilite port=labels bundle=control
#pragma HLS INTERFACE s_axilite port=queue_item bundle=control
#pragma HLS INTERFACE s_axilite port=output bundle=control
#pragma HLS INTERFACE s_axilite port=status bundle=control
#pragma HLS INTERFACE s_axilite port=capacity bundle=control
#pragma HLS INTERFACE s_axilite port=epoch bundle=control
#pragma HLS INTERFACE s_axilite port=operation bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
 dieroute::NativeSearchLabelSlot value{};
 auto result=dieroute::NativeSearchLabelOpStatus::invalid;
 if(operation==1)result=dieroute::native_search_label_read<1024>(labels,capacity,epoch,queue_item->node,value);
 if(operation==2)result=dieroute::native_search_label_close<1024>(labels,capacity,epoch,*queue_item,value);
 if(result==dieroute::NativeSearchLabelOpStatus::ok)*output=value;
 *status=std::uint32_t(result);
}
