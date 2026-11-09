#include "native_search_hbm_snapshot_search.hpp"
extern "C" void dieroute_native_snapshot_search_hbm(const std::uint64_t* offsets,const std::uint64_t* arcs,const std::uint64_t* policy,const dieroute::SummaryWord* resources,const std::uint64_t* authority_control,const std::uint64_t* potential,dieroute::NativeSearchLabelSlot* labels,dieroute::NativeSearchQueueEntry* queue,dieroute::NativeSearchResourceObservation* journal,std::uint64_t* metadata,const std::uint64_t* configuration,std::uint64_t* result_words,std::uint64_t* goal_words){
#pragma HLS INTERFACE m_axi port=offsets offset=slave bundle=graph_memory depth=13
#pragma HLS INTERFACE m_axi port=arcs offset=slave bundle=graph_memory depth=64
#pragma HLS INTERFACE m_axi port=policy offset=slave bundle=graph_memory depth=12
#pragma HLS INTERFACE m_axi port=potential offset=slave bundle=graph_memory depth=12
#pragma HLS INTERFACE m_axi port=resources offset=slave bundle=authority_memory depth=48
#pragma HLS INTERFACE m_axi port=authority_control offset=slave bundle=authority_memory depth=8
#pragma HLS INTERFACE m_axi port=labels offset=slave bundle=scratch_memory depth=1024
#pragma HLS INTERFACE m_axi port=queue offset=slave bundle=scratch_memory depth=1024
#pragma HLS INTERFACE m_axi port=journal offset=slave bundle=scratch_memory depth=1024
#pragma HLS INTERFACE m_axi port=metadata offset=slave bundle=scratch_memory depth=8
#pragma HLS INTERFACE m_axi port=configuration offset=slave bundle=scratch_memory depth=16
#pragma HLS INTERFACE m_axi port=result_words offset=slave bundle=scratch_memory depth=8
#pragma HLS INTERFACE m_axi port=goal_words offset=slave bundle=scratch_memory depth=8
#pragma HLS INTERFACE s_axilite port=offsets bundle=control
#pragma HLS INTERFACE s_axilite port=arcs bundle=control
#pragma HLS INTERFACE s_axilite port=policy bundle=control
#pragma HLS INTERFACE s_axilite port=resources bundle=control
#pragma HLS INTERFACE s_axilite port=authority_control bundle=control
#pragma HLS INTERFACE s_axilite port=potential bundle=control
#pragma HLS INTERFACE s_axilite port=labels bundle=control
#pragma HLS INTERFACE s_axilite port=queue bundle=control
#pragma HLS INTERFACE s_axilite port=journal bundle=control
#pragma HLS INTERFACE s_axilite port=metadata bundle=control
#pragma HLS INTERFACE s_axilite port=configuration bundle=control
#pragma HLS INTERFACE s_axilite port=result_words bundle=control
#pragma HLS INTERFACE s_axilite port=goal_words bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
 // configuration: nodes,arcs,dies,shard,tree,net,sink,session,revision,
 // epoch,expansion_limit,max_hops,label_capacity,queue_capacity,journal_capacity,potential_enabled.
 for(unsigned i=0;i<16;++i){if(i==1||i==7||i==8||i==9||i==10)continue;if(configuration[i]>UINT32_MAX){result_words[0]=std::uint64_t(dieroute::NativeSnapshotStatus::invalid);return;}}
 if(configuration[12]>2097152||configuration[13]>8388608||configuration[14]>33554432||configuration[15]>1||metadata[0]>UINT32_MAX||metadata[1]>UINT32_MAX||metadata[2]>UINT32_MAX){result_words[0]=std::uint64_t(dieroute::NativeSnapshotStatus::invalid);return;}
 dieroute::SummaryWord control{};for(unsigned i=0;i<8;++i)control.w[i]=authority_control[i];
 auto queued=std::uint32_t(metadata[0]),used=std::uint32_t(metadata[1]),touched=std::uint32_t(metadata[2]);
 auto result=dieroute::native_search_snapshot<134217728,536870912,33554432,2097152>(offsets,arcs,policy,resources,control,configuration[15]?potential:nullptr,labels,configuration[12],queue,configuration[13],queued,journal,configuration[14],used,touched,configuration[0],configuration[1],configuration[2],configuration[3],configuration[4],configuration[5],configuration[6],configuration[7],configuration[8],configuration[9],configuration[10],configuration[11]);
 metadata[0]=queued;metadata[1]=used;metadata[2]=touched;
 result_words[0]=std::uint64_t(result.status);result_words[1]=result.expanded;result_words[2]=result.edge_visits;result_words[3]=result.raw_arcs;result_words[4]=queued;result_words[5]=used;result_words[6]=touched;result_words[7]=0;
 if(result.status==dieroute::NativeSnapshotStatus::found){goal_words[0]=result.goal.epoch;goal_words[1]=result.goal.cost;goal_words[2]=result.goal.version;goal_words[3]=result.goal.node;goal_words[4]=result.goal.hops;goal_words[5]=result.goal.parent;goal_words[6]=result.goal.edge;goal_words[7]=result.goal.flags;}
}
