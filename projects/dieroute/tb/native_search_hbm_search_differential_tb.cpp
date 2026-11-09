#include "native_search_hbm_frontier.hpp"
#include "native_search_hbm_relax_observed.hpp"
#include "sparse_search.hpp"
#include <array>
#include <cassert>
#include <optional>
#include <random>
#include <vector>
using namespace dieroute;
struct Arc{std::uint32_t dst,edge;};
int main(){
 std::mt19937_64 rng(928314);
 for(unsigned trial=0;trial<1000;++trial){
  const unsigned nodes=4+rng()%28,sink=nodes-1;
  std::vector<std::vector<Arc>> graph(nodes);
  std::vector<NativeSearchResourceObservation> observations(nodes);
  for(unsigned n=0;n<nodes;++n){observations[n]={n,rng()%100,rng()%10,rng()%10,7,1,n%3,0};for(unsigned d=0;d<nodes;++d)if(d!=n&&rng()%5==0)graph[n].push_back({d,n*nodes+d});}
  std::vector<std::uint32_t> expected_reads;
  SparseSearch reference;
  auto expected=reference.run(nodes,{{0,0,0}},sink,UINT32_MAX,[&](std::uint32_t n,auto offer){for(auto arc:graph[n])offer(arc.dst,arc.edge,[&]()->std::optional<std::uint64_t>{auto o=observations[arc.dst];expected_reads.push_back(arc.dst);return 1+o.history+3*o.occupancy;});});
  std::array<NativeSearchLabelSlot,1024> labels{};
  std::array<NativeSearchQueueEntry,1024> queue{};
  std::array<NativeSearchResourceObservation,1024> journal{};
  labels[0]={1,0,1,0,0,UINT32_MAX,UINT32_MAX,2};queue[0]={0,0,0,0,UINT32_MAX};
  std::uint32_t queued=1,used=0;std::uint64_t expanded=0,visits=0;
  bool found=false;
  while(true){
   NativeSearchLabelSlot current{};auto status=native_search_take_frontier<1024>(labels.data(),1024,queue.data(),1024,queued,1,current);
   if(status==NativeFrontierStatus::empty)break;
   if(status==NativeFrontierStatus::skipped)continue;
   assert(status==NativeFrontierStatus::current);++expanded;
   if(current.node==sink){found=true;break;}
   for(auto arc:graph[current.node]){
    ++visits;
    auto result=native_search_relax_observed<1024>(labels.data(),1024,queue.data(),1024,queued,current,arc.dst,arc.edge,observations[arc.dst],7,journal.data(),1024,used,false,3,0,UINT64_MAX,true);
    assert(result==NativeObservedRelaxStatus::accepted||result==NativeObservedRelaxStatus::dominated||result==NativeObservedRelaxStatus::protected_label);
   }
  }
  assert(found==(expected.status==SparseSearchStatus::found));
  assert(expanded==expected.expanded&&visits==expected.edge_visits&&used==expected_reads.size());
  for(unsigned i=0;i<used;++i){assert(journal[i].node==expected_reads[i]);auto o=observations[expected_reads[i]];assert(journal[i].version==o.version&&journal[i].occupancy==o.occupancy&&journal[i].history==o.history);}
  if(found){
   assert(labels[sink].cost==expected.cost&&labels[sink].hops==expected.hops);
   std::vector<std::uint32_t> path,edges;auto n=sink;
   for(unsigned count=0;;++count){assert(count<nodes);auto value=labels[n];if(value.parent==UINT32_MAX)break;path.push_back(n);edges.push_back(value.edge);n=value.parent;}
   std::reverse(path.begin(),path.end());std::reverse(edges.begin(),edges.end());assert(n==expected.attachment&&path==expected.path&&edges==expected.edges);
  }
 }
}
