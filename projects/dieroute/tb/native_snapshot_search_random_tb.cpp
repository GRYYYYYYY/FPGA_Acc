#include "native_search_hbm_snapshot_search.hpp"
#include "native_search_hbm_seed.hpp"
#include "sparse_search.hpp"
#include <array>
#include <random>
#include <iostream>
#include <cassert>
#include <cstring>
using namespace dieroute;
// Synthetic scalar authority headers only. This does not validate member chains
// or stand in for the separate commit-produced authority integration tests.
int main(){std::mt19937_64 rng(716293);unsigned found=0,exhausted=0;std::uint64_t read_count=0;
 for(unsigned trial=0;trial<1000;++trial){
  unsigned count=4+rng()%28,shift=trial%64;auto id=[&](unsigned n){return std::uint32_t(n*128+shift);};auto nodes=id(count-1)+1;
  std::vector<std::vector<std::pair<unsigned,unsigned>>> graph(count);std::vector<std::uint64_t> policy(nodes,UINT32_MAX|(std::uint64_t(1)<<32)|(std::uint64_t(1)<<40)),offsets(nodes+1),arcs;
  std::vector<unsigned> occupancy(count),history(count),owners(count);std::array<SummaryWord,192> resources{};SummaryWord control{};control.w[0]=1;control.w[1]=7;control.w[2]=1+rng()%8;control.w[5]=nodes|(std::uint64_t(3)<<32);control.w[6]=64|(std::uint64_t(64)<<32);control.w[7]=256;std::uint64_t member_head=0;
  for(unsigned n=0;n<count;++n){auto mask=unsigned(1+rng()%7),owner=0u;while(!(mask&(1u<<owner)))++owner;owners[n]=owner;occupancy[n]=n? rng()%5:1;history[n]=rng()%20;
   auto exclusive=(n&&n!=count-1&&rng()%9==0)?99u:UINT32_MAX;bool forbidden=n&&n!=count-1&&rng()%13==0;policy[id(n)]=exclusive|(std::uint64_t(mask)<<32)|(std::uint64_t(forbidden)<<40);
   auto hash=(id(n)*UINT32_C(2654435761))&63u;auto slot=owner*64+hash;while(resources[slot].w[0])slot=owner*64+((slot-owner*64+1)&63);
   auto& r=resources[slot];r.w[0]=1;r.w[1]=occupancy[n];r.w[2]=history[n];r.w[3]=100+n;r.w[4]=id(n)|(std::uint64_t(mask)<<32);r.w[5]=occupancy[n]?member_head:UINT64_MAX;member_head+=occupancy[n];
   for(unsigned d=0;d<count;++d)if(d!=n&&rng()%6==0)graph[n].push_back({id(d),n*count+d});
  }
  control.w[3]=member_head;control.w[4]=UINT64_MAX;
  for(unsigned n=0;n<nodes;++n){offsets[n]=arcs.size();if(n>=shift&&(n-shift)%128==0){auto logical=(n-shift)/128;for(auto edge:graph[logical])arcs.push_back(edge.first|(std::uint64_t(edge.second)<<32));}}offsets[nodes]=arcs.size();
  auto allowed=[&](unsigned dst){auto p=policy[dst];return !(p&(std::uint64_t(1)<<40))&&(unsigned(p)==UINT32_MAX||unsigned(p)==30);};
  std::vector<unsigned> expected_reads;SparseSearch reference;auto expected=reference.run(nodes,{{id(0),0,0}},id(count-1),UINT32_MAX,[&](unsigned node,auto offer){for(auto edge:graph[(node-shift)/128])if(allowed(edge.first))offer(edge.first,edge.second,[&,dst=edge.first](){auto n=(dst-shift)/128;expected_reads.push_back(dst);return std::optional<std::uint64_t>(1+history[n]+control.w[2]*occupancy[n]);});});
  std::array<NativeSearchLabelSlot,64> labels{};std::array<NativeSearchQueueEntry,1024> queue{};std::array<NativeSearchResourceObservation,1024> journal{};std::uint32_t queued=0,used=0,touched=1;NativeSearchLabelSlot seed{5,0,0,id(0),0,UINT32_MAX,UINT32_MAX,0},output{};
  assert(native_search_seed<1024>(labels.data(),64,queue.data(),1024,queued,seed,0,UINT64_MAX,true,output)==NativeSeedStatus::accepted);
  auto saved_resources=resources;auto result=native_search_snapshot<4096,1024,1024,64>(offsets.data(),arcs.data(),policy.data(),resources.data(),control,nullptr,labels.data(),64,queue.data(),1024,queued,journal.data(),1024,used,touched,nodes,arcs.size(),3,64,256,30,id(count-1),1,7,5,UINT64_MAX,UINT32_MAX);
  assert(unsigned(result.status)==unsigned(expected.status)&&result.expanded==expected.expanded&&result.edge_visits==expected.edge_visits&&used==expected_reads.size());assert(!std::memcmp(resources.data(),saved_resources.data(),sizeof(resources)));
  for(unsigned i=0;i<used;++i){auto n=(expected_reads[i]-shift)/128;assert(journal[i].node==expected_reads[i]&&journal[i].version==100+n&&journal[i].occupancy==occupancy[n]&&journal[i].history==history[n]&&journal[i].owner==owners[n]&&journal[i].session==1&&journal[i].epoch==5);}read_count+=used;
  if(result.status==NativeSnapshotStatus::found){++found;assert(result.goal.cost==expected.cost&&result.goal.hops==expected.hops);std::vector<unsigned> path,edges;auto node=id(count-1);for(unsigned steps=0;;++steps){assert(steps<count);auto loc=native_search_label_lookup<1024>(labels.data(),64,5,node);assert(loc.status==NativeLabelLookup::found);auto value=labels[loc.slot];if(value.parent==UINT32_MAX)break;path.push_back(node);edges.push_back(value.edge);node=value.parent;}std::reverse(path.begin(),path.end());std::reverse(edges.begin(),edges.end());assert(node==expected.attachment&&path==expected.path&&edges==expected.edges);}else{assert(result.status==NativeSnapshotStatus::exhausted);++exhausted;}
 }
 std::cout<<"{\"status\":\"passed\",\"cases\":1000,\"found\":"<<found<<",\"exhausted\":"<<exhausted<<",\"observations\":"<<read_count<<"}\n";
}
