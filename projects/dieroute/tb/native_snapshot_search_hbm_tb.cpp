#include "net_commit_fixture.hpp"
#include "native_search_hbm_snapshot_search.hpp"
#include "native_search_hbm_seed.hpp"
#include "sparse_search.hpp"
using namespace commit_test;
extern "C" void dieroute_native_snapshot_search_hbm(const std::uint64_t* offsets,const std::uint64_t* arcs,const std::uint64_t* policy,const dieroute::SummaryWord* resources,const std::uint64_t* authority_control,const std::uint64_t* potential,dieroute::NativeSearchLabelSlot* labels,dieroute::NativeSearchQueueEntry* queue,dieroute::NativeSearchResourceObservation* journal,std::uint64_t* metadata,const std::uint64_t* configuration,std::uint64_t* result_words,std::uint64_t* goal_words);
int main(){Fixture f;f.request(commit_initialize);f.run();f.start(0,10,0);f.start(1,20,4);f.start(2,30,8);
 f.request(commit_proposal,0,10);f.footprint({1,3,5,7,9});f.branch(0,{1,3,5,7,9},0);f.run();f.request(commit_proposal,1,20);f.footprint({6,7});f.branch(4,{6,7},1);f.run();
 std::array<std::uint64_t,12> potentials{4,3,UINT64_MAX,2,2,1,1,0,2,UINT64_MAX,1,UINT64_MAX};
 auto compare=[&](unsigned sink,unsigned capacity,std::uint64_t limit,unsigned hops,bool guided){
  std::array<NativeSearchLabelSlot,1024> labels{};std::array<NativeSearchQueueEntry,1024> queue{};std::array<NativeSearchResourceObservation,1024> journal{};std::uint32_t queued=0,used=0,touched=1;
  NativeSearchLabelSlot seed{3,0,0,8,0,UINT32_MAX,UINT32_MAX,0},output{};auto potential=[&](unsigned n){return guided?potentials[n]:std::uint64_t(0);};check(native_search_seed<1024>(labels.data(),capacity,queue.data(),1024,queued,seed,potential(8),UINT64_MAX,true,output)==NativeSeedStatus::accepted,"seed");
  std::vector<unsigned> reads;SparseSearch reference;auto expected=reference.run_guided(12,{{8,0,0}},sink,hops,[&](unsigned node,auto offer){for(auto i=f.offsets[node];i<f.offsets[node+1];++i){auto dst=unsigned(f.arcs[i]),edge=unsigned(f.arcs[i]>>32);auto p=f.policy[dst];if(p&(std::uint64_t(1)<<40))continue;if(unsigned(p)!=UINT32_MAX&&unsigned(p)!=30)continue;offer(dst,edge,[&,dst](){reads.push_back(dst);auto r=f.resource(dst);return std::optional<std::uint64_t>(1+(r?r->w[2]:0)+f.control.w[2]*(r?r->w[1]:0));});}},potential,{capacity,limit});
  auto before=f.state();alignas(64) std::uint64_t configuration[16]={12,f.arc_count,3,16,64,30,sink,1,f.control.w[1],3,limit,hops,capacity,1024,1024,guided?1u:0u};alignas(64) std::uint64_t metadata[8]={queued,used,touched},words[8]{},goal[8]{};
  dieroute_native_snapshot_search_hbm(f.offsets.data(),f.arcs.data(),f.policy.data(),f.resources.data(),f.control.w,potentials.data(),labels.data(),queue.data(),journal.data(),metadata,configuration,words,goal);
  queued=metadata[0];used=metadata[1];touched=metadata[2];NativeSnapshotResult result{};result.status=NativeSnapshotStatus(words[0]);result.expanded=words[1];result.edge_visits=words[2];result.raw_arcs=words[3];
  if(result.status==NativeSnapshotStatus::found)result.goal={goal[0],goal[1],goal[2],std::uint32_t(goal[3]),std::uint32_t(goal[4]),std::uint32_t(goal[5]),std::uint32_t(goal[6]),std::uint32_t(goal[7])};
  check(before==f.state(),"search mutated authority");check(unsigned(result.status)==unsigned(expected.status),"status differential");check(result.expanded==expected.expanded&&result.edge_visits==expected.edge_visits&&used==reads.size(),"search accounting differential");
  for(unsigned i=0;i<used;++i){auto r=f.resource(reads[i]);check(journal[i].node==reads[i]&&journal[i].version==(r?r->w[3]:0)&&journal[i].occupancy==(r?r->w[1]:0)&&journal[i].history==(r?r->w[2]:0),"consumed observation differential");}
  if(result.status==NativeSnapshotStatus::found){check(result.goal.cost==expected.cost&&result.goal.hops==expected.hops,"goal differential");std::vector<unsigned> path,edges;auto n=sink;for(unsigned i=0;;++i){check(i<12,"trace cycle");auto loc=native_search_label_lookup<1024>(labels.data(),capacity,3,n);check(loc.status==NativeLabelLookup::found,"trace lookup");auto value=labels[loc.slot];if(value.parent==UINT32_MAX)break;path.push_back(n);edges.push_back(value.edge);n=value.parent;}std::reverse(path.begin(),path.end());std::reverse(edges.begin(),edges.end());check(n==expected.attachment&&path==expected.path&&edges==expected.edges,"path differential");}
 };
 compare(7,16,UINT64_MAX,UINT32_MAX,false);compare(7,16,UINT64_MAX,UINT32_MAX,true);compare(7,2,UINT64_MAX,UINT32_MAX,false);compare(7,16,1,UINT32_MAX,false);compare(7,16,0,UINT32_MAX,false);compare(7,16,UINT64_MAX,1,false);compare(0,16,UINT64_MAX,UINT32_MAX,false);
 f.request(commit_negotiate);f.command[0].w[7]=1;f.command[1].w[4]=2;f.run();compare(7,16,UINT64_MAX,UINT32_MAX,false);compare(7,16,UINT64_MAX,UINT32_MAX,true);
}
