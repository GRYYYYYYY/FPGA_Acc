#include "persistroute.hpp"
#include "multiqueue.hpp"
#include <cassert>
#include <iostream>
#include <vector>
using namespace persistroute;
int main(){
 std::vector<Node> nodes(MAX_RESOURCES);nodes[0]={0,2,0};nodes[1]={2,1,0};nodes[2]={3,1,0};nodes[3]={4,0,0};
 std::vector<Edge> edges(MAX_EDGES);edges[0]={1,10,1};edges[1]={2,2,1};edges[2]={3,10,1};edges[3]={3,2,1};
 std::vector<Resource> resources(MAX_RESOURCES,Resource{0,1,0,0,0,0xffffffffU});
 std::vector<Task> tasks(MAX_TASKS);tasks[0]={9,12,0,3,0,16,0,0,0};
 std::vector<std::uint32_t> paths(MAX_TX_ENTRIES),dist(MAX_RESOURCES),pred(MAX_RESOURCES),hops(MAX_RESOURCES),seen(MAX_RESOURCES),closed(MAX_RESOURCES),read_epoch(MAX_RESOURCES),sizes(MQ_QUEUES);
 std::vector<ReadEntry> reads(MAX_TX_ENTRIES);std::vector<PathResult> results(MAX_TASKS);std::vector<MQEntry> queue(MQ_QUEUES*MQ_DEPTH);Metrics metrics{};
 search_hbm_kernel(nodes.data(),edges.data(),resources.data(),tasks.data(),paths.data(),reads.data(),results.data(),dist.data(),pred.data(),hops.data(),seen.data(),closed.data(),read_epoch.data(),queue.data(),sizes.data(),4,4,1,8,32,&metrics);
 if(results[0].status!=1||results[0].length!=2||paths[0]!=2||paths[1]!=3){
  std::cerr<<"search_hbm_tb: FAIL status="<<results[0].status<<" length="<<results[0].length
           <<" offset="<<results[0].offset<<" read_offset="<<results[0].read_offset
           <<" read_count="<<results[0].read_count<<" path0="<<paths[0]<<" path1="<<paths[1]
           <<" expanded="<<metrics.expanded<<" edge_visits="<<metrics.edge_visits
           <<" failed="<<metrics.failed<<'\n';
  std::cerr<<"queue_sizes:";
  for(std::uint32_t bank=0;bank<MQ_QUEUES;++bank)std::cerr<<' '<<sizes[bank];
  std::cerr<<"\nwork:";
  for(std::uint32_t node=0;node<4;++node){
   std::cerr<<" ["<<node<<" d="<<dist[node]<<" p="<<pred[node]<<" h="<<hops[node]
            <<" seen="<<seen[node]<<" closed="<<closed[node]<<" read="<<read_epoch[node]<<']';
  }
  std::cerr<<'\n';return 1;
 }
 tasks[0].epoch=2;tasks[0].reserved=64;queue[64]={0,0xffffffffU,0,0};queue[65]={2,0xffffffffU,0,1};
 results[0]={};metrics={};
 search_hbm_kernel(nodes.data(),edges.data(),resources.data(),tasks.data(),paths.data(),reads.data(),results.data(),dist.data(),pred.data(),hops.data(),seen.data(),closed.data(),read_epoch.data(),queue.data(),sizes.data(),4,4,1,8,32,&metrics);
 if(results[0].status!=1||results[0].length!=2||paths[0]!=2||paths[1]!=3){
  std::cerr<<"search_hbm_tb: FAIL multi-source status="<<results[0].status
           <<" length="<<results[0].length<<" attachment="<<paths[0]<<" sink="<<paths[1]<<'\n';return 1;
 }
 std::cout<<"search_hbm_tb: PASS\n";
}
