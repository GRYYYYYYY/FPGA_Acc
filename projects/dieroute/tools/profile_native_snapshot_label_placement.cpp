#include "native_csr_io.hpp"
#include "native_search_hbm_snapshot_search.hpp"
#include "native_search_hbm_seed.hpp"
#include "sparse_search.hpp"
#include <iostream>
#include <memory>
#include <unordered_map>
using namespace dieroute;
using namespace dieroute::native;
extern "C" void dieroute_native_snapshot_search_hbm(const std::uint64_t*,const std::uint64_t*,const std::uint64_t*,const SummaryWord*,const std::uint64_t*,const std::uint64_t*,NativeSearchLabelSlot*,NativeSearchQueueEntry*,NativeSearchResourceObservation*,std::uint64_t*,const std::uint64_t*,std::uint64_t*,std::uint64_t*);
int main(int argc,char** argv){try{
 check(argc==9,"usage: probe SEARCH POLICY SNAPSHOT ARCH NET SINK LABELS EXPANSIONS");auto arch=fingerprint(argv[4]);fs::path snap=argv[3];
 Container offsets(fs::path(argv[1])/"offsets.bin",offsets_type,8,arch),arcs(fs::path(argv[1])/"arcs.bin",arcs_type,8,arch),policy(argv[2],0x44520026,8,arch);
 Mapping rm(snap/"resources.raw"),cm(snap/"control.raw"),sm(snap/"tree_seeds.raw");check(cm.bytes==64&&sm.bytes%64==0,"raw widths");SummaryWord control{};std::memcpy(&control,cm.data,64);
 auto nodes=std::uint32_t(control.w[5]),dies=std::uint32_t(control.w[5]>>32),shard=std::uint32_t(control.w[6]),tree=std::uint32_t(control.w[7]);
 auto net=std::stoul(argv[5]),sink=std::stoul(argv[6]),cap=std::stoul(argv[7]);auto limit=std::stoull(argv[8]);check(cap&&cap<=2097152&&policy.count==nodes&&offsets.count==nodes+1&&rm.bytes==std::uint64_t(dies)*shard*64,"shape");
 std::unordered_map<std::uint32_t,SummaryWord> authority;
 for(size_t i=0;i<rm.bytes/64;++i){SummaryWord r{};std::memcpy(&r,rm.data+i*64,64);if(r.w[0]==control.w[0])check(authority.emplace(std::uint32_t(r.w[4]),r).second,"duplicate resource");}
 std::vector<SparseSeed> seeds;for(size_t i=0;i<sm.bytes/64;++i){SummaryWord r{};std::memcpy(&r,sm.data+i*64,64);seeds.push_back({std::uint32_t(r.w[1]),std::uint32_t(r.w[5]),0});}
 std::vector<NativeSearchResourceObservation> reads;std::uint64_t occupied=0;
 auto allowed=[&](std::uint32_t n){check(n<nodes,"destination range");auto p=le64(policy.data+n*8);return !(p&(UINT64_C(1)<<40))&&(std::uint32_t(p)==UINT32_MAX||std::uint32_t(p)==net);};
 SparseSearch ref;auto expected=ref.run(nodes,seeds,sink,UINT32_MAX,[&](std::uint32_t n,auto offer){for(auto i=offsets.offset(n);i<offsets.offset(n+1);++i){auto dst=arcs.dst(i);if(!allowed(dst))continue;offer(dst,arcs.edge(i),[&,dst](){auto it=authority.find(dst);auto r=it==authority.end()?SummaryWord{}:it->second;auto p=le64(policy.data+dst*8);unsigned owner=0;while(!((p>>32)&(1u<<owner)))++owner;
 reads.push_back({dst,r.w[3],r.w[1],r.w[2],control.w[0],1,owner,0});occupied+=r.w[1]!=0;
 check(r.w[2]<UINT64_MAX-1&&(!r.w[1]||control.w[2]<=(UINT64_MAX-2-r.w[2])/r.w[1]),"reference cost overflow");return std::optional<std::uint64_t>(1+r.w[2]+control.w[2]*r.w[1]);});}},{cap,limit});
 std::cerr<<"reference complete expanded="<<expected.expanded<<" reads="<<reads.size()<<"\n";
 std::vector<std::uint32_t> ids;std::unordered_map<std::uint32_t,bool> seen;
 for(auto seed:seeds)if(seen.emplace(seed.node,true).second)ids.push_back(seed.node);
 for(auto r:reads)if(seen.emplace(std::uint32_t(r.node),true).second)ids.push_back(std::uint32_t(r.node));
 auto observed_unique=ids.size();if(ids.size()>cap)ids.resize(cap);
 auto profile=[&](bool mixed){std::vector<std::uint32_t> next(cap+1);for(std::uint32_t i=0;i<=cap;++i)next[i]=i;
 auto find=[&](std::uint32_t v){auto root=v;while(next[root]!=root)root=next[root];while(next[v]!=v){auto n=next[v];next[v]=root;v=n;}return root;};
 std::uint64_t total=0,maximum=0;for(auto id:ids){std::uint64_t x=id;if(mixed){x=(x^(x>>16))*UINT32_C(0x7feb352d);x=(x^(x>>15))*UINT32_C(0x846ca68b);x=x^(x>>16);}auto start=std::uint32_t(x%cap);auto slot=find(start);if(slot==cap)slot=find(0);check(slot<cap,"full profile table");auto probes=std::uint64_t(slot>=start?slot-start:cap-start+slot)+1;total+=probes;maximum=std::max(maximum,probes);next[slot]=find(slot+1);}return std::make_pair(total,maximum);};
 auto direct=profile(false),mixed=profile(true);
 std::cout<<"{\"status\":\"profiled\",\"unique_nodes\":"<<ids.size()<<",\"observed_unique_nodes\":"<<observed_unique<<",\"reference_status\":"<<unsigned(expected.status)<<",\"direct_insert_probes\":"<<direct.first<<",\"direct_max_probe\":"<<direct.second<<",\"mixed_insert_probes\":"<<mixed.first<<",\"mixed_max_probe\":"<<mixed.second<<",\"scope\":\"Exact insertion-only placement probes for first-observed unique nodes, not all runtime lookups or HBM timing\"}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
