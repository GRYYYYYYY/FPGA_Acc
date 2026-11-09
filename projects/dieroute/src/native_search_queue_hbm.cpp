#include "native_search_hbm_queue.hpp"
extern "C" void dieroute_native_search_queue_hbm(
    dieroute::NativeSearchQueueEntry* entries,
    const dieroute::NativeSearchQueueEntry* input,
    dieroute::NativeSearchQueueEntry* output,
    std::uint32_t* count,std::uint32_t* status,
    std::uint32_t capacity,std::uint32_t operation){
#pragma HLS INTERFACE m_axi port=entries offset=slave bundle=queue_memory depth=1024
#pragma HLS INTERFACE m_axi port=input offset=slave bundle=commands depth=1
#pragma HLS INTERFACE m_axi port=output offset=slave bundle=commands depth=1
#pragma HLS INTERFACE m_axi port=count offset=slave bundle=metadata depth=1
#pragma HLS INTERFACE m_axi port=status offset=slave bundle=metadata depth=1
#pragma HLS INTERFACE s_axilite port=entries bundle=control
#pragma HLS INTERFACE s_axilite port=input bundle=control
#pragma HLS INTERFACE s_axilite port=output bundle=control
#pragma HLS INTERFACE s_axilite port=count bundle=control
#pragma HLS INTERFACE s_axilite port=status bundle=control
#pragma HLS INTERFACE s_axilite port=capacity bundle=control
#pragma HLS INTERFACE s_axilite port=operation bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
    auto used=*count;
    if(!capacity||capacity>1024||used>capacity||(operation!=1&&operation!=2)){*status=2;return;}
    if(operation==1){
        if(used==capacity){*status=1;return;}
        const auto value=*input;auto index=used;
        while(index){auto parent=(index-1)/2;if(!dieroute::native_search_queue_less(value,entries[parent]))break;entries[index]=entries[parent];index=parent;}
        entries[index]=value;*count=used+1;*status=0;
    }else{
        if(!used){*status=1;return;}
        *output=entries[0];const auto last=entries[used-1];--used;
        if(used){std::uint32_t index=0;while(index<used/2){auto child=index*2+1;if(child+1<used&&dieroute::native_search_queue_less(entries[child+1],entries[child]))++child;if(!dieroute::native_search_queue_less(entries[child],last))break;entries[index]=entries[child];index=child;}entries[index]=last;}
        *count=used;*status=0;
    }
}
