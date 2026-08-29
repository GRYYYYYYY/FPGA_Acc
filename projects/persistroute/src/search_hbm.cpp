#include "persistroute.hpp"
#include "multiqueue.hpp"

namespace persistroute {
extern "C" void search_hbm_kernel(const Node* nodes,const Edge* edges,const Resource* resources,const Task* tasks,
 std::uint32_t* path_pool,ReadEntry* read_pool,PathResult* results,std::uint32_t* distance,
 std::uint32_t* predecessor,std::uint32_t* hop_count,std::uint32_t* seen_epoch,std::uint32_t* closed_epoch,
 std::uint32_t* read_epoch,MQEntry* queue_data,std::uint32_t* queue_sizes,std::uint32_t node_count,
 std::uint32_t edge_count,std::uint32_t task_count,std::uint32_t queue_depth,
 std::uint32_t transaction_capacity,Metrics* metrics){
#ifdef __SYNTHESIS__
#pragma HLS INTERFACE m_axi port=nodes depth=8192 bundle=graph
#pragma HLS INTERFACE m_axi port=edges depth=65536 bundle=graph
#pragma HLS INTERFACE m_axi port=resources depth=8192 bundle=state
#pragma HLS INTERFACE m_axi port=tasks depth=1024 bundle=state
#pragma HLS INTERFACE m_axi port=path_pool depth=4096 bundle=path
#pragma HLS INTERFACE m_axi port=read_pool depth=4096 bundle=result
#pragma HLS INTERFACE m_axi port=results depth=1024 bundle=result
#pragma HLS INTERFACE m_axi port=distance depth=8192 bundle=work
#pragma HLS INTERFACE m_axi port=predecessor depth=8192 bundle=work
#pragma HLS INTERFACE m_axi port=hop_count depth=8192 bundle=work
#pragma HLS INTERFACE m_axi port=seen_epoch depth=8192 bundle=work
#pragma HLS INTERFACE m_axi port=closed_epoch depth=8192 bundle=work
#pragma HLS INTERFACE m_axi port=read_epoch depth=8192 bundle=work
#pragma HLS INTERFACE m_axi port=queue_data depth=2048 bundle=qdata
#pragma HLS INTERFACE m_axi port=queue_sizes depth=8 bundle=qmeta
#pragma HLS INTERFACE m_axi port=metrics depth=1 bundle=result
#pragma HLS INTERFACE s_axilite port=node_count bundle=control
#pragma HLS INTERFACE s_axilite port=edge_count bundle=control
#pragma HLS INTERFACE s_axilite port=task_count bundle=control
#pragma HLS INTERFACE s_axilite port=queue_depth bundle=control
#pragma HLS INTERFACE s_axilite port=transaction_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
#endif
 Metrics out{};std::uint32_t path_cursor=0,read_cursor=0;
 for(std::uint32_t n=0;n<node_count;++n){
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE II=3
#endif
  seen_epoch[n]=closed_epoch[n]=read_epoch[n]=0;
 }
 for(std::uint32_t ti=0;ti<task_count;++ti){const Task t=tasks[ti];const std::uint32_t epoch=ti+1;
  PathResult result{0,0,0,0,0,0};std::uint32_t path_entries=0;bool overflow=false,found=false;
  if(t.source>=node_count||t.sink>=node_count){result.offset=path_cursor;result.read_offset=read_cursor;result.status=3;results[ti]=result;++out.failed;continue;}
  hbm_mq_init(queue_sizes);
  if(t.epoch==0){seen_epoch[t.source]=epoch;distance[t.source]=0;predecessor[t.source]=0xffffffffU;hop_count[t.source]=0;
   overflow=!hbm_mq_push(queue_data,queue_sizes,queue_depth,{t.source,0xffffffffU,0,t.source});}
  else for(std::uint32_t seed_index=0;seed_index<t.epoch&&!overflow;++seed_index){
   const MQEntry seed=queue_data[t.reserved+seed_index];if(seed.node>=node_count||seed.tie>t.max_hops){overflow=true;break;}
   if(seen_epoch[seed.node]!=epoch||seed.cost_q<distance[seed.node]||
      (seed.cost_q==distance[seed.node]&&seed.tie<hop_count[seed.node])){
    seen_epoch[seed.node]=epoch;distance[seed.node]=seed.cost_q;predecessor[seed.node]=0xffffffffU;hop_count[seed.node]=seed.tie;
    overflow=!hbm_mq_push(queue_data,queue_sizes,queue_depth,{seed.node,0xffffffffU,seed.cost_q,seed.node});}
  }
  MQEntry current{};
  while(!overflow&&hbm_mq_pop(queue_data,queue_sizes,queue_depth,current)){
   if(current.node>=node_count||seen_epoch[current.node]!=epoch||closed_epoch[current.node]==epoch||current.cost_q!=distance[current.node])continue;
   closed_epoch[current.node]=epoch;++out.expanded;if(current.node==t.sink){found=true;break;}
   if(hop_count[current.node]>=t.max_hops)continue;
   const Node node=nodes[current.node];
   for(std::uint32_t j=0;j<node.edge_count;++j){
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE II=1
#endif
    const std::uint32_t ei=node.edge_begin+j;if(ei>=edge_count){overflow=true;break;}const Edge edge=edges[ei];
    // Multi-source tree nodes are immutable attachment candidates.  With nonzero
    // upstream seed costs, allowing relaxation back into another seed can return
    // a branch that re-enters the authoritative tree.
    const bool existing_seed=edge.dst<node_count&&seen_epoch[edge.dst]==epoch&&predecessor[edge.dst]==0xffffffffU;
    if(edge.dst>=node_count||closed_epoch[edge.dst]==epoch||existing_seed)continue;
    ++out.edge_visits;const Resource state=resources[edge.dst];
    const bool other_net=state.owner!=t.net_id;
    const std::uint32_t projected=static_cast<std::uint32_t>(state.occupancy)+(other_net?1U:0U);
    const std::uint32_t overuse=projected>state.capacity?projected-state.capacity:0U;
    const std::uint64_t congestion=static_cast<std::uint64_t>(edge.base_cost_q)+
     (other_net?static_cast<std::uint64_t>(state.history_cost_q)+
                static_cast<std::uint64_t>(state.present_cost_q)*overuse:0ULL);
    const std::uint64_t timing=static_cast<std::uint64_t>(edge.delay_q)*t.criticality_q/65535U;
    const std::uint64_t total=static_cast<std::uint64_t>(current.cost_q)+congestion+timing;
    const std::uint32_t candidate=total>0xffffffffULL?0xffffffffU:static_cast<std::uint32_t>(total);const std::uint32_t candidate_hops=hop_count[current.node]+1;
    if(seen_epoch[edge.dst]!=epoch||candidate<distance[edge.dst]||
       (candidate==distance[edge.dst]&&(candidate_hops<hop_count[edge.dst]||
        (candidate_hops==hop_count[edge.dst]&&current.node<predecessor[edge.dst])))){
     seen_epoch[edge.dst]=epoch;distance[edge.dst]=candidate;predecessor[edge.dst]=current.node;hop_count[edge.dst]=candidate_hops;
     if(!hbm_mq_push(queue_data,queue_sizes,queue_depth,{edge.dst,current.node,candidate,edge.dst})){overflow=true;break;}
    }
   }
  }
  // Only committed path resources can invalidate feasibility. Logging every explored
  // node needlessly caps large searches at the 16-bit transaction count.
  if(found&&!overflow){std::uint32_t cursor=t.sink;while(predecessor[cursor]!=0xffffffffU){if(cursor>=node_count||path_cursor>=transaction_capacity||read_cursor>=transaction_capacity||path_entries>=65535U){overflow=true;break;}path_pool[path_cursor++]=cursor;read_pool[read_cursor++]={cursor,resources[cursor].version};++path_entries;++result.read_count;cursor=predecessor[cursor];}
   if(!overflow&&t.epoch!=0){if(path_cursor>=transaction_capacity||read_cursor>=transaction_capacity||path_entries>=65535U)overflow=true;else{path_pool[path_cursor++]=cursor;read_pool[read_cursor++]={cursor,resources[cursor].version};++path_entries;++result.read_count;}}
   if(!overflow){for(std::uint32_t left=0;left<path_entries/2;++left){const std::uint32_t li=path_cursor-path_entries+left,ri=path_cursor-1-left;const std::uint32_t tmp=path_pool[li];path_pool[li]=path_pool[ri];path_pool[ri]=tmp;}result.length=static_cast<std::uint16_t>(path_entries);result.status=1;}}
  if(!found||overflow){path_cursor-=path_entries;read_cursor-=result.read_count;result.length=0;result.read_count=0;result.status=3;++out.failed;}
  result.offset=path_cursor-result.length;result.read_offset=read_cursor-result.read_count;results[ti]=result;
 }
 *metrics=out;
}
}
