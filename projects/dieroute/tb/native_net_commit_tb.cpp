#include "net_commit_fixture.hpp"
#include "native_net_transaction.hpp"
#include <numeric>
#include <memory>
using namespace commit_test;
static void parity(const Fixture& f,const NativeRouteState& state){
 for(unsigned n=0;n<f.policy.size();++n){auto a=f.resource(n);auto b=state.find_use(n);check((a?a->w[1]:0)==(b?b->nets.size():0)&&(a?a->w[2]:0)==(b?b->history:0)&&(a?a->w[3]:0)==(b?b->version:0),"native authority tuple differs");check(f.members(n)==(b?b->nets:std::set<std::uint32_t>{}),"native exact membership differs");}
 for(unsigned slot=0;slot<3;++slot){auto id=unsigned(f.nets[slot].w[1]);if(!state.trees().count(id))continue;auto t=f.tree(slot);const auto& gold=state.tree(id);check(f.nets[slot].w[2]==gold.source&&t.size()==gold.nodes.size(),"native tree shape differs");
  for(const auto& [n,v]:gold.nodes){const auto& got=t.at(n);check(got.w[3]==v.parent&&got.w[4]==v.pip&&got.w[5]==v.depth,"native tree parent/PIP/depth differs");}}
}
static NativeNetProposal proposal(const Fixture& f,const NativeRouteState& state,unsigned slot,const std::vector<unsigned>& path){
 NativeNetProposal p;p.net=unsigned(f.nets[slot].w[1]);p.present=f.control.w[2];p.snapshot=std::make_shared<const NativeRouteState>(state);NativeRouteState staged(state);
 NativeNetBranch b;b.task={0,path.empty()?state.tree(p.net).source:path.back(),0};b.result.status=SparseSearchStatus::found;b.result.attachment=state.tree(p.net).source;b.result.path=path;b.result.hops=path.size();auto from=b.result.attachment;
 for(auto n:path){b.result.edges.push_back(f.edges.at({from,n}));b.result.cost+=staged.cost(n,p.net,p.present);p.reads.push_back(n);from=n;}
 p.reads.push_back(11);std::sort(p.reads.begin(),p.reads.end());p.reads.erase(std::unique(p.reads.begin(),p.reads.end()),p.reads.end());p.branches.push_back(b);return p;
}
static void pack(Fixture& f,const NativeNetProposal& p,unsigned slot,std::uint64_t generation){
 f.request(commit_proposal,slot,p.net);f.command[0].w[5]=generation;f.command[0].w[6]=p.present;f.command[1].w[0]=p.reads.size();
 for(unsigned i=0;i<p.reads.size();++i){f.reads[i*2]=p.reads[i];auto v=p.snapshot->find_use(p.reads[i]);f.reads[i*2+1]=v?v->version:0;}
 for(const auto& b:p.branches){auto& dest=f.branches[f.command[1].w[2]++];dest.w[0]=b.result.attachment;dest.w[1]=b.task.sink;dest.w[2]=f.command[1].w[3];dest.w[3]=b.result.path.size();dest.w[4]=b.result.hops;dest.w[5]=b.result.cost;
  for(unsigned i=0;i<b.result.path.size();++i){auto cursor=f.command[1].w[3]++;f.paths[cursor*2]=b.result.path[i]|(std::uint64_t(b.result.edges[i])<<32);}}
 for(const auto& r:p.shadow_reads){auto& d=f.shadows[f.command[1].w[1]++];d.w[0]=r.node;d.w[1]=r.worker;d.w[2]=r.seen.occupancy;d.w[3]=r.seen.history;d.w[4]=r.seen.version;}
}
int main(){try{
 Fixture f;auto layout=NativeOwnerLayout::from_membership(3,[&](unsigned n){return unsigned(f.policy.at(n)>>32&255);});NativeRouteState state(layout);auto allowed=[](auto,auto){return true;};auto edge=[&](auto a,auto b,auto pip){auto p=f.edges.find({a,b});return p!=f.edges.end()&&p->second==pip;};
 f.request(commit_initialize);f.run();for(unsigned i=0;i<3;++i){f.start(i,(i+1)*10,i*4);state.start((i+1)*10,i*4,allowed);}parity(f,state);
 const std::vector<unsigned> route[3][2]={{{1,3,5,7,9},{2,11}},{{6,7,9},{3,5,7,9}},{{10,7,9},{11}}};
 unsigned accepted=0,rejected=0,stale_shadows=0;
 auto commit=[&](NativeNetProposal& p,unsigned slot,std::uint64_t generation){auto v=native_validate_net(state,p,f.control.w[2]);pack(f,p,slot,generation);f.run(v.valid()?commit_ok:commit_conflict);
  check(f.completion.w[2]==p.reads.size()&&f.completion.w[3]==v.conflicts.size()&&f.completion.w[4]==v.stale_shadows.size()&&f.completion.w[5]==v.tree_changed,"native validation classification differs");
  auto ok=native_commit_net(state,p,f.control.w[2],allowed,edge);check(ok==v.valid(),"native commit differs");accepted+=ok;rejected+=!ok;stale_shadows+=v.stale_shadows.size();parity(f,state);
 };
 for(unsigned round=0;round<32;++round){
  unsigned a=round%3,b=(a+1)%3;
  for(auto slot:{a,b}){f.request(commit_ripup,slot,(slot+1)*10);f.run();state.ripup((slot+1)*10);parity(f,state);}
  auto earlier=proposal(f,state,a,route[a][round%2]);auto generation=f.nets[a].w[5];
  auto other=proposal(f,state,b,route[b][(round/2)%2]);commit(other,b,f.nets[b].w[5]);
  commit(earlier,a,generation);
  if(!native_validate_net(state,earlier,f.control.w[2]).valid()&&state.tree((a+1)*10).nodes.size()==1){auto fresh=proposal(f,state,a,route[a][round%2]);commit(fresh,a,f.nets[a].w[5]);}
  f.request(commit_negotiate);f.command[0].w[7]=1;f.command[1].w[4]=1+(round%7);f.run();state.negotiate(1);parity(f,state);
 }
 // Isolate a consumed-shadow mismatch while all resource read versions match.
 f.request(commit_ripup,0,10);f.run();state.ripup(10);auto p=proposal(f,state,0,route[0][0]);auto v=NativeWorkerShadows::authority(state,7);++v.history;p.shadow_reads.push_back({0,2,7,v,true});commit(p,0,f.nets[0].w[5]);
 check(rejected&&accepted&&stale_shadows==1,"differential test lacks rejection/commit coverage");
 // A second valid branch attaches to a node created by the first branch.
 auto multi=proposal(f,state,0,{1,3});auto first=multi.branches[0];NativeRouteState staged(state);staged.accept(10,3,first.result,allowed,edge);NativeNetBranch last;last.task={1,9,2};last.result.status=SparseSearchStatus::found;last.result.attachment=3;last.result.path={5,7,9};last.result.edges={f.edges.at({3,5}),f.edges.at({5,7}),f.edges.at({7,9})};last.result.hops=5;for(auto n:last.result.path){last.result.cost+=staged.cost(n,10,f.control.w[2]);multi.reads.push_back(n);}multi.branches.push_back(last);std::sort(multi.reads.begin(),multi.reads.end());multi.reads.erase(std::unique(multi.reads.begin(),multi.reads.end()),multi.reads.end());commit(multi,0,f.nets[0].w[5]);
 std::cout<<"native whole-net differential passed: calls="<<f.calls<<" commits="<<accepted<<" rejects="<<rejected<<" stale_shadows="<<stale_shadows<<'\n';
 // Stream the actual observed worst-case footprint length, including absent
 // interior resources. This is a C-model bound test, not a throughput result.
 const std::uint32_t count=2823767;std::vector<std::uint64_t> policy(count,UINT32_MAX|(UINT64_C(1)<<32)),offsets(count+1,0),reads(std::uint64_t(count)*2);
 for(std::uint32_t n=0;n<count;++n){reads[std::uint64_t(n)*2]=n;reads[std::uint64_t(n)*2+1]=n==0?1:0;}
 Fixture large;auto invoke=[&]{dieroute_net_commit_hbm(large.command.data(),policy.data(),offsets.data(),large.arcs.data(),reads.data(),large.shadows.data(),large.branches.data(),large.paths.data(),large.resources.data(),large.trees.data(),large.nets.data(),&large.control,large.scratch.data(),large.deltas.data(),&large.completion,count,0,3,16,8,64,count,16,16,32,128,32);};
 large.request(commit_initialize);invoke();check(large.completion.w[0]==0,"long-read init");large.request(commit_start,0,10);invoke();check(large.completion.w[0]==0,"long-read root");large.request(commit_validate,0,10);large.command[1].w[0]=count;invoke();check(large.completion.w[0]==0&&large.completion.w[2]==count,"long footprint truncated");auto before=large.state();reads.back()=1;invoke();check(large.completion.w[0]==commit_conflict&&large.completion.w[2]==count&&large.completion.w[3]==1&&large.state()==before,"last off-path read not validated atomically");
 std::cout<<"full 2823767-entry streamed footprint and last-entry conflict passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
