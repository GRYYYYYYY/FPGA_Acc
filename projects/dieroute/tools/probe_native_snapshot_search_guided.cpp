#include "native_csr_io.hpp"
#include "native_search_hbm_snapshot_search.hpp"
#include "native_search_hbm_seed.hpp"
#include "sparse_search.hpp"
#include "native_quotient.hpp"
#include <iostream>
#include <memory>
#include <unordered_map>
using namespace dieroute;
using namespace dieroute::native;
extern "C" void dieroute_native_snapshot_search_hbm(const std::uint64_t*,const std::uint64_t*,const std::uint64_t*,const SummaryWord*,const std::uint64_t*,const std::uint64_t*,NativeSearchLabelSlot*,NativeSearchQueueEntry*,NativeSearchResourceObservation*,std::uint64_t*,const std::uint64_t*,std::uint64_t*,std::uint64_t*);
int main(int argc,char** argv){try{
 check(argc==11,"usage: probe SEARCH POLICY SNAPSHOT ARCH NET SINK LABELS EXPANSIONS ARTIFACT_OUT QUOTIENT");auto arch=fingerprint(argv[4]);fs::path snap=argv[3];
 Container offsets(fs::path(argv[1])/"offsets.bin",offsets_type,8,arch),arcs(fs::path(argv[1])/"arcs.bin",arcs_type,8,arch),policy(argv[2],0x44520026,8,arch);
 Mapping rm(snap/"resources.raw"),cm(snap/"control.raw"),sm(snap/"tree_seeds.raw");check(cm.bytes==64&&sm.bytes%64==0,"raw widths");SummaryWord control{};std::memcpy(&control,cm.data,64);
 auto nodes=std::uint32_t(control.w[5]),dies=std::uint32_t(control.w[5]>>32),shard=std::uint32_t(control.w[6]),tree=std::uint32_t(control.w[7]);
 auto net=std::stoul(argv[5]),sink=std::stoul(argv[6]),cap=std::stoul(argv[7]);auto limit=std::stoull(argv[8]);check(cap&&cap<=2097152&&policy.count==nodes&&offsets.count==nodes+1&&rm.bytes==std::uint64_t(dies)*shard*64,"shape");
 std::unordered_map<std::uint32_t,SummaryWord> authority;
 for(size_t i=0;i<rm.bytes/64;++i){SummaryWord r{};std::memcpy(&r,rm.data+i*64,64);if(r.w[0]==control.w[0])check(authority.emplace(std::uint32_t(r.w[4]),r).second,"duplicate resource");}
 std::vector<SparseSeed> seeds;for(size_t i=0;i<sm.bytes/64;++i){SummaryWord r{};std::memcpy(&r,sm.data+i*64,64);seeds.push_back({std::uint32_t(r.w[1]),std::uint32_t(r.w[5]),0});}
 std::vector<NativeSearchResourceObservation> reads;std::uint64_t occupied=0;
 auto allowed=[&](std::uint32_t n){check(n<nodes,"destination range");auto p=le64(policy.data+n*8);return !(p&(UINT64_C(1)<<40))&&(std::uint32_t(p)==UINT32_MAX||std::uint32_t(p)==net);};
 QuotientPotential quotient(argv[10],arch,nodes);check(!seeds.empty(),"empty seeds");quotient.prepare(sink,seeds[0].node);
 std::vector<std::uint64_t> potential(nodes);for(std::uint32_t n=0;n<nodes;++n)potential[n]=quotient(n);check(potential[sink]==0,"sink potential");
 std::uint64_t checked_edges=0;for(std::uint32_t n=0;n<nodes;++n)if(allowed(n)){for(auto i=offsets.offset(n);i<offsets.offset(n+1);++i){auto dst=arcs.dst(i);if(!allowed(dst))continue;++checked_edges;check(potential[dst]==UINT64_MAX||(potential[n]!=UINT64_MAX&&potential[n]<=potential[dst]+1),"inconsistent quotient potential");}}
 std::cerr<<"potential consistency verified edges="<<checked_edges<<" quotient_expanded="<<quotient.expanded<<"\n";
 SparseSearch ref;auto expected=ref.run_guided(nodes,seeds,sink,UINT32_MAX,[&](std::uint32_t n,auto offer){for(auto i=offsets.offset(n);i<offsets.offset(n+1);++i){auto dst=arcs.dst(i);if(!allowed(dst))continue;offer(dst,arcs.edge(i),[&,dst](){auto it=authority.find(dst);auto r=it==authority.end()?SummaryWord{}:it->second;auto p=le64(policy.data+dst*8);unsigned owner=0;while(!((p>>32)&(1u<<owner)))++owner;
 reads.push_back({dst,r.w[3],r.w[1],r.w[2],control.w[0],1,owner,0});occupied+=r.w[1]!=0;
 check(r.w[2]<UINT64_MAX-1&&(!r.w[1]||control.w[2]<=(UINT64_MAX-2-r.w[2])/r.w[1]),"reference cost overflow");return std::optional<std::uint64_t>(1+r.w[2]+control.w[2]*r.w[1]);});}},[&](std::uint32_t n){return potential[n];},{cap,limit});
 std::cerr<<"reference complete expanded="<<expected.expanded<<" reads="<<reads.size()<<"\n";
 auto qcap=std::uint32_t(std::max<unsigned long>(1024,cap*4)),jcap=std::uint32_t(std::max<unsigned long>(1024,cap*16));
 auto labels=std::make_unique<NativeSearchLabelSlot[]>(cap);auto queue=std::make_unique<NativeSearchQueueEntry[]>(qcap);auto journal=std::make_unique<NativeSearchResourceObservation[]>(jcap);std::uint32_t queued=0;
 for(auto s:seeds){NativeSearchLabelSlot input{},out{};input.epoch=1;input.node=s.node;input.hops=s.hops;input.cost=0;check(native_search_seed<33554432>(labels.get(),cap,queue.get(),qcap,queued,input,potential[s.node],UINT64_MAX,true,out)==NativeSeedStatus::accepted,"seed rejected");}
 std::uint64_t meta[8]={queued,0,seeds.size()},cfg[16]={nodes,arcs.count,dies,shard,tree,net,sink,control.w[0],control.w[1],1,limit,UINT32_MAX,cap,qcap,jcap,1},result[8]{},goal[8]{};
 dieroute_native_snapshot_search_hbm(reinterpret_cast<const std::uint64_t*>(offsets.data),reinterpret_cast<const std::uint64_t*>(arcs.data),reinterpret_cast<const std::uint64_t*>(policy.data),reinterpret_cast<const SummaryWord*>(rm.data),control.w,potential.data(),labels.get(),queue.get(),journal.get(),meta,cfg,result,goal);
 auto expected_status=expected.status==SparseSearchStatus::found?0:expected.status==SparseSearchStatus::exhausted?1:expected.status==SparseSearchStatus::budget_exhausted?2:3;
 check(result[0]==std::uint64_t(expected_status)&&result[1]==expected.expanded&&result[2]==expected.edge_visits&&meta[1]==reads.size(),"search counters/status mismatch");
 for(size_t i=0;i<reads.size();++i)check(std::memcmp(&reads[i],&journal[i],64)==0,"ordered authority observation mismatch");
 auto save=[&](const char* name,const void* data,size_t bytes){if(argc==11){fs::path out=argv[9];fs::create_directories(out);check(!fs::exists(out/name),"artifact already exists");std::ofstream f(out/name,std::ios::binary);f.write(static_cast<const char*>(data),bytes);check(bool(f),"artifact write");}};
 save("observations.raw",journal.get(),meta[1]*64);save("goal.raw",goal,64);save("result.raw",result,64);
 if(expected_status==0){check(goal[1]==expected.cost&&goal[4]==expected.hops,"goal mismatch");std::vector<std::uint32_t> path,edges;auto n=std::uint32_t(sink);for(size_t i=0;;++i){check(i<=meta[2],"parent cycle");auto loc=native_search_label_lookup<33554432>(labels.get(),cap,1,n);check(loc.status==NativeLabelLookup::found,"trace missing");auto l=labels[loc.slot];if(l.parent==UINT32_MAX){check(n==expected.attachment,"attachment mismatch");break;}path.push_back(n);edges.push_back(l.edge);n=l.parent;}std::reverse(path.begin(),path.end());std::reverse(edges.begin(),edges.end());check(path==expected.path&&edges==expected.edges,"path mismatch");save("path_nodes.raw",path.data(),path.size()*4);save("path_pips.raw",edges.data(),edges.size()*4);std::uint64_t attachment=n;save("attachment.raw",&attachment,8);}
 std::cout<<"{\"status\":\"passed\",\"search_status\":"<<result[0]<<",\"expanded\":"<<result[1]<<",\"observations\":"<<meta[1]<<",\"occupied_observations\":"<<occupied<<",\"cost\":"<<goal[1]<<",\"scope\":\"Actual whole-search top C-model, real graph and commit-produced authority; no RTL or board claim\"}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
