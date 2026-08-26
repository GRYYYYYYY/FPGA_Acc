#include "persistroute.hpp"
#include "multiqueue.hpp"
namespace persistroute {
extern "C" void search_kernel(const Node nodes[MAX_RESOURCES],const Edge edges[MAX_EDGES],const Resource resources[MAX_RESOURCES],const Task tasks[MAX_TASKS],std::uint32_t path_pool[MAX_TX_ENTRIES],ReadEntry read_pool[MAX_TX_ENTRIES],PathResult results[MAX_TASKS],std::uint32_t node_count,std::uint32_t edge_count,std::uint32_t task_count,Metrics* metrics){
#ifdef __SYNTHESIS__
#pragma HLS INTERFACE m_axi port=nodes bundle=gmem0
#pragma HLS INTERFACE m_axi port=edges bundle=gmem1
#pragma HLS INTERFACE m_axi port=resources bundle=gmem2
#pragma HLS INTERFACE m_axi port=tasks bundle=gmem3
#pragma HLS INTERFACE m_axi port=path_pool bundle=gmem4
#pragma HLS INTERFACE m_axi port=read_pool bundle=gmem5
#pragma HLS INTERFACE m_axi port=results bundle=gmem6
#pragma HLS INTERFACE s_axilite port=node_count bundle=control
#pragma HLS INTERFACE s_axilite port=edge_count bundle=control
#pragma HLS INTERFACE s_axilite port=task_count bundle=control
#pragma HLS INTERFACE m_axi port=metrics bundle=gmem7
#pragma HLS INTERFACE s_axilite port=return bundle=control
#endif
 Metrics out{};std::uint32_t path_cursor=0,read_cursor=0;
 if(node_count>MAX_RESOURCES||edge_count>MAX_EDGES||task_count>MAX_TASKS){*metrics=out;return;}
 static std::uint32_t distance[MAX_RESOURCES],predecessor[MAX_RESOURCES];
 static std::uint8_t closed[MAX_RESOURCES],read_seen[MAX_RESOURCES];
 static std::uint32_t reverse_path[MAX_PATH];
 for(std::uint32_t ti=0;ti<task_count;++ti){const Task t=tasks[ti];PathResult r{0,0,0,0,0,0};
  if(t.source>=node_count||t.sink>=node_count){r.offset=path_cursor;r.read_offset=read_cursor;r.status=3;results[ti]=r;++out.failed;continue;}
  for(std::uint32_t n=0;n<node_count;++n){
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE II=1
#endif
   distance[n]=0xffffffffU;predecessor[n]=0xffffffffU;closed[n]=0;read_seen[n]=0;}
  MultiQueue queue;mq_init(queue);distance[t.source]=0;mq_push(queue,{t.source,0xffffffffU,0,t.source});MQEntry current{};bool found=false;
  while(mq_pop(queue,current)){
   if(current.node>=node_count||closed[current.node]||current.cost_q!=distance[current.node]) continue;
   closed[current.node]=1;++out.expanded;if(current.node==t.sink){found=true;break;}const Node n=nodes[current.node];
   for(std::uint32_t j=0;j<n.edge_count;++j){
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE II=1
#endif
    const std::uint32_t ei=n.edge_begin+j;if(ei>=edge_count)break;const Edge e=edges[ei];if(e.dst>=node_count||closed[e.dst])continue;++out.edge_visits;const Resource s=resources[e.dst];
    if(!read_seen[e.dst]){if(read_cursor>=MAX_TX_ENTRIES){continue;}read_seen[e.dst]=1;read_pool[read_cursor++]={e.dst,s.version};++r.read_count;}
    const bool other_net=s.owner!=t.net_id;const std::uint64_t congestion=e.base_cost_q+(other_net?s.present_cost_q+s.history_cost_q:0)+(other_net&&s.occupancy>=s.capacity?4096:0);const std::uint64_t timing=static_cast<std::uint64_t>(e.delay_q)*t.criticality_q/65535U;const std::uint64_t sum=static_cast<std::uint64_t>(current.cost_q)+congestion+timing;const std::uint32_t candidate=sum>0xffffffffULL?0xffffffffU:static_cast<std::uint32_t>(sum);
    if(candidate<distance[e.dst]||(candidate==distance[e.dst]&&current.node<predecessor[e.dst])){distance[e.dst]=candidate;predecessor[e.dst]=current.node;if(!mq_push(queue,{e.dst,current.node,candidate,e.dst})){continue;}}}
  }
  std::uint32_t length=0;if(found){for(std::uint32_t n=t.sink;n!=t.source&&n!=0xffffffffU&&length<MAX_PATH;n=predecessor[n])reverse_path[length++]=n;if(length==MAX_PATH||predecessor[reverse_path[length-1]]==0xffffffffU){found=false;}}
  if(found&&path_cursor+length<=MAX_TX_ENTRIES){for(std::uint32_t j=0;j<length;++j)path_pool[path_cursor+j]=reverse_path[length-1-j];path_cursor+=length;r.length=static_cast<std::uint16_t>(length);r.status=1;}else{r.status=3;++out.failed;}r.offset=path_cursor-r.length;r.read_offset=read_cursor-r.read_count;results[ti]=r;}
 *metrics=out;
}
extern "C" void commit_kernel(Resource resources[MAX_RESOURCES],const Task tasks[MAX_TASKS],const std::uint32_t path_pool[MAX_TX_ENTRIES],const ReadEntry read_pool[MAX_TX_ENTRIES],PathResult results[MAX_TASKS],std::uint32_t resource_count,std::uint32_t task_count,Metrics* metrics){
#ifdef __SYNTHESIS__
#pragma HLS INTERFACE m_axi port=resources bundle=gmem0
#pragma HLS INTERFACE m_axi port=tasks bundle=gmem1
#pragma HLS INTERFACE m_axi port=path_pool bundle=gmem2
#pragma HLS INTERFACE m_axi port=read_pool bundle=gmem3
#pragma HLS INTERFACE m_axi port=results bundle=gmem4
#pragma HLS INTERFACE s_axilite port=resource_count bundle=control
#pragma HLS INTERFACE s_axilite port=task_count bundle=control
#pragma HLS INTERFACE m_axi port=metrics bundle=gmem5
#pragma HLS INTERFACE s_axilite port=return bundle=control
#endif
 Metrics out{};if(resource_count>MAX_RESOURCES||task_count>MAX_TASKS){*metrics=out;return;}
 for(std::uint32_t ti=0;ti<task_count;++ti){PathResult r=results[ti];if(r.status!=1)continue;bool valid=true;
  for(std::uint32_t j=0;j<r.read_count;++j){
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE II=1
#endif
   const ReadEntry x=read_pool[r.read_offset+j];if(x.resource_id>=resource_count||(resources[x.resource_id].version!=x.version&&resources[x.resource_id].owner!=tasks[ti].net_id)){valid=false;break;}}
  if(!valid){r.status=2;++out.conflicts;results[ti]=r;continue;}
  for(std::uint32_t j=0;j<r.length;++j){const std::uint32_t id=path_pool[r.offset+j];Resource& s=resources[id];if(s.owner!=tasks[ti].net_id){++s.occupancy;++s.version;s.owner=tasks[ti].net_id;}}
  r.status=4;++out.commits;results[ti]=r;}
 *metrics=out;
}
}
