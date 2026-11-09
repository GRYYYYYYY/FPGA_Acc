#include "native_csr_io.hpp"
#include "native_search_hbm_frontier.hpp"
#include "native_search_hbm_relax_observed.hpp"
#include "native_search_hbm_seed.hpp"
#include "native_search_hbm_csr.hpp"
#include "sparse_search.hpp"
#include "native_quotient.hpp"
#include <iostream>
#include <memory>
using namespace dieroute;
using namespace dieroute::native;
#ifdef DIEROUTE_PROBE_HLS_TOP
extern "C" void dieroute_native_search_relax_observed_hbm(dieroute::NativeSearchLabelSlot* labels,dieroute::NativeSearchQueueEntry* queue,dieroute::NativeSearchResourceObservation* journal,const dieroute::NativeSearchLabelSlot* parent,const std::uint64_t* observation_words,std::uint64_t* metadata,std::uint32_t label_capacity,std::uint32_t queue_capacity,std::uint32_t journal_capacity,std::uint32_t dst,std::uint32_t edge,std::uint64_t session,std::uint32_t own,std::uint64_t present,std::uint64_t potential,std::uint64_t max_cost,std::uint32_t credit);
#endif
#ifdef DIEROUTE_PROBE_WORKER_TOP
extern "C" void dieroute_native_search_worker_hbm(dieroute::NativeSearchLabelSlot* labels,dieroute::NativeSearchQueueEntry* queue,dieroute::NativeSearchResourceObservation* journal,const dieroute::NativeSearchLabelSlot* parent,const std::uint64_t* observation_words,std::uint64_t* metadata,std::uint32_t label_capacity,std::uint32_t queue_capacity,std::uint32_t journal_capacity,std::uint32_t dst,std::uint32_t edge,std::uint64_t session,std::uint32_t own,std::uint64_t present,std::uint64_t potential,std::uint64_t max_cost,std::uint32_t credit,dieroute::NativeSearchLabelSlot* frontier_output,std::uint32_t operation);
#endif
#ifdef DIEROUTE_PROBE_CSR_TOP
extern "C" void dieroute_native_search_csr_hbm(const std::uint64_t*,const std::uint64_t*,const std::uint64_t*,std::uint64_t*,std::uint64_t*,std::uint32_t,std::uint64_t,std::uint32_t,std::uint32_t,std::uint32_t,std::uint64_t);
#endif
int main(int argc,char** argv){try{
 check(argc==7||argc==8||argc==9,"usage: probe_native_hbm_search SEARCH FOOTPRINT MAPPING ARCH TASK LABEL_BUDGET [QUOTIENT [POLICY]]");
 fs::path search=argv[1];auto arch=fingerprint(argv[4]);auto task=std::stoul(argv[5]),budget=std::stoul(argv[6]);check(budget>0&&budget<=2097152,"label budget");
 Container offsets(search/"offsets.bin",offsets_type,8,arch),arcs(search/"arcs.bin",arcs_type,8,arch),mask(search/"node_protection.bin",0x4452000a,1,arch),owner(search/"exclusive_net.bin",0x4452000b,4,arch);
 Raw tasks(fs::path(argv[2])/"tasks.bin",8),mapping(fs::path(argv[3])/"footprint_node_map.bin",1);
 check(task<tasks.count&&tasks.at(task,0)==task,"task identity");auto net=tasks.at(task,1),src=mapping.at(tasks.at(task,2),0),sink=mapping.at(tasks.at(task,3),0);
 auto nodes=mask.count;check(nodes<UINT32_MAX&&owner.count==nodes&&offsets.count==nodes+1&&offsets.offset(nodes)==arcs.count,"CSR shape");
#ifdef DIEROUTE_PROBE_CSR_TOP
 check(argc==9,"CSR top requires native policy container");Container csr_policy(argv[8],0x44520026,8,arch);check(csr_policy.count==nodes,"policy coverage");
#endif
 auto allowed=[&](std::uint32_t n){check(n<nodes,"node range");
#ifdef DIEROUTE_PROBE_CSR_TOP
 auto word=le64(csr_policy.data+n*8);check(std::uint32_t(word)==le32(owner.data+n*4),"policy exclusive-net identity");check(!mask.data[n]||(word&(std::uint64_t(1)<<40)),"policy protection identity");return !(word&(std::uint64_t(1)<<40))&&(std::uint32_t(word)==none||std::uint32_t(word)==net);
#else
 return !mask.data[n]&&(le32(owner.data+4*n)==none||le32(owner.data+4*n)==net);
#endif
};check(allowed(src)&&allowed(sink),"endpoint permission");
 std::uint64_t csr_calls=0,csr_scanned=0;
 auto expand_reference=[&](std::uint32_t n,auto offer){auto begin=offsets.offset(n),end=offsets.offset(n+1);check(begin<=end&&end<=arcs.count,"CSR row");for(auto i=begin;i<end;++i){auto dst=arcs.dst(i);if(allowed(dst))offer(dst,arcs.edge(i));}};
#ifdef DIEROUTE_PROBE_CSR_TOP

 auto expand=[&](std::uint32_t n,auto offer){alignas(64) std::uint64_t state[8]={offsets.offset(n),0,99},out[8]{};
  while(true){dieroute_native_search_csr_hbm(reinterpret_cast<const std::uint64_t*>(offsets.data),reinterpret_cast<const std::uint64_t*>(arcs.data),reinterpret_cast<const std::uint64_t*>(csr_policy.data),state,out,nodes,arcs.count,3,n,net,64);
   ++csr_calls;csr_scanned+=state[1];auto status=NativeCSRStatus(state[2]);check(status!=NativeCSRStatus::invalid,"native CSR top rejection");if(status==NativeCSRStatus::arc)offer(std::uint32_t(out[0]),std::uint32_t(out[1]));if(status==NativeCSRStatus::end)break;
  }
 };
#else
 auto expand=expand_reference;
#endif
 std::unique_ptr<QuotientPotential> quotient;if(argc>=8){quotient=std::make_unique<QuotientPotential>(argv[7],arch,nodes);quotient->prepare(sink,src);}
 auto potential=[&](std::uint32_t n){return quotient?(*quotient)(n):std::uint64_t(0);};
 std::vector<std::uint32_t> reads;SparseSearch reference;
 auto expected=reference.run_guided(nodes,{{src,0,0}},sink,UINT32_MAX,[&](std::uint32_t n,auto offer){expand_reference(n,[&](std::uint32_t dst,std::uint32_t edge){offer(dst,edge,[&,dst](){reads.push_back(dst);return std::optional<std::uint64_t>(1);});});},potential,{budget,UINT64_MAX});
 const std::uint32_t queue_capacity=std::max<std::uint32_t>(1048576,budget*4),journal_capacity=std::max<std::uint32_t>(1048576,budget*16);
 auto labels=std::make_unique<NativeSearchLabelSlot[]>(budget);auto queue=std::make_unique<NativeSearchQueueEntry[]>(queue_capacity);auto journal=std::make_unique<NativeSearchResourceObservation[]>(journal_capacity);
 std::uint32_t queued=0,used=0,touched=0;
#ifdef DIEROUTE_PROBE_WORKER_TOP
 NativeSearchLabelSlot seed{};seed.epoch=1;seed.node=src;seed.cost=0;seed.hops=0;NativeSearchLabelSlot seed_output{};
 alignas(64) std::uint64_t seed_words[8]{};alignas(64) std::uint64_t seed_metadata[8]{};
 dieroute_native_search_worker_hbm(labels.get(),queue.get(),journal.get(),&seed,seed_words,seed_metadata,budget,queue_capacity,journal_capacity,0,0,7,0,0,potential(src),UINT64_MAX,1,&seed_output,4);
 check(seed_metadata[2]==std::uint64_t(NativeSeedStatus::accepted)||seed_metadata[2]==std::uint64_t(NativeSeedStatus::unreachable),"seed failure");queued=seed_metadata[0];touched=queued?1:0;
#else
 labels[src%budget]={1,0,1,src,0,UINT32_MAX,UINT32_MAX,2};queue[0]={potential(src),0,0,src,UINT32_MAX};queued=potential(src)==UINT64_MAX?0:1;touched=queued?1:0;
#endif
std::uint64_t expanded=0,visits=0;auto status=SparseSearchStatus::exhausted;
 while(true){NativeSearchLabelSlot current{};NativeFrontierStatus f;
#ifdef DIEROUTE_PROBE_WORKER_TOP
  NativeSearchLabelSlot epoch_input{};epoch_input.epoch=1;alignas(64) std::uint64_t words[8]{};alignas(64) std::uint64_t metadata[8]={queued,used,99};
  dieroute_native_search_worker_hbm(labels.get(),queue.get(),journal.get(),&epoch_input,words,metadata,budget,queue_capacity,journal_capacity,0,0,7,0,0,0,UINT64_MAX,1,&current,2);
  queued=metadata[0];check(metadata[1]==used,"frontier journal mutation");f=NativeFrontierStatus(metadata[2]);
#else
  f=native_search_take_frontier<67108864>(labels.get(),budget,queue.get(),queue_capacity,queued,1,current);
#endif
 if(f==NativeFrontierStatus::empty){break;}
 if(f==NativeFrontierStatus::skipped){continue;}
 check(f==NativeFrontierStatus::current,"frontier failure");++expanded;
  if(current.node==sink){status=SparseSearchStatus::found;break;}bool cutoff=false;
  expand(current.node,[&](std::uint32_t dst,std::uint32_t edge){if(cutoff)return;++visits;auto before=native_search_label_lookup<67108864>(labels.get(),budget,1,dst);NativeSearchResourceObservation o{dst,0,0,0,7,1,0,0};NativeObservedRelaxStatus r;
#if defined(DIEROUTE_PROBE_HLS_TOP) || defined(DIEROUTE_PROBE_WORKER_TOP)
   alignas(64) std::uint64_t words[8];std::memcpy(words,&o,sizeof(o));alignas(64) std::uint64_t metadata[8]={queued,used,99};
   #ifdef DIEROUTE_PROBE_WORKER_TOP
   NativeSearchLabelSlot unused{};dieroute_native_search_worker_hbm(labels.get(),queue.get(),journal.get(),&current,words,metadata,budget,queue_capacity,journal_capacity,dst,edge,7,0,0,potential(dst),UINT64_MAX,touched<budget?1:0,&unused,1);
   #else
   dieroute_native_search_relax_observed_hbm(labels.get(),queue.get(),journal.get(),&current,words,metadata,budget,queue_capacity,journal_capacity,dst,edge,7,0,0,potential(dst),UINT64_MAX,touched<budget?1:0);
   #endif
   queued=metadata[0];used=metadata[1];r=NativeObservedRelaxStatus(metadata[2]);
#else
   r=native_search_relax_observed<67108864>(labels.get(),budget,queue.get(),queue_capacity,queued,current,dst,edge,o,7,journal.get(),journal_capacity,used,false,0,potential(dst),UINT64_MAX,touched<budget);
#endif

   if(r==NativeObservedRelaxStatus::label_capacity){cutoff=true;return;}check(r==NativeObservedRelaxStatus::accepted||r==NativeObservedRelaxStatus::dominated||r==NativeObservedRelaxStatus::protected_label||r==NativeObservedRelaxStatus::unreachable,"arc failure");if(r==NativeObservedRelaxStatus::accepted&&before.status!=NativeLabelLookup::found)++touched;
  });if(cutoff){status=SparseSearchStatus::budget_exhausted;break;}
 }
 check(status==expected.status&&expanded==expected.expanded&&visits==expected.edge_visits&&used==reads.size(),"search differential mismatch");for(unsigned i=0;i<used;++i)check(journal[i].node==reads[i]&&journal[i].occupancy==0&&journal[i].history==0,"observation mismatch");
 if(status==SparseSearchStatus::found){std::vector<std::uint32_t> path,edges;auto n=sink;for(unsigned i=0;;++i){check(i<=touched,"parent cycle");NativeSearchLabelSlot v{};
#ifdef DIEROUTE_PROBE_WORKER_TOP
 NativeSearchLabelSlot trace_input{};trace_input.epoch=1;trace_input.node=n;alignas(64) std::uint64_t trace_words[8]{};alignas(64) std::uint64_t trace_metadata[8]={queued,used,99};
 dieroute_native_search_worker_hbm(labels.get(),queue.get(),journal.get(),&trace_input,trace_words,trace_metadata,budget,queue_capacity,journal_capacity,0,0,7,0,0,0,UINT64_MAX,1,&v,3);
 check(trace_metadata[2]==std::uint64_t(NativeSearchLabelOpStatus::ok)&&trace_metadata[0]==queued&&trace_metadata[1]==used,"trace failure");
#else
 auto loc=native_search_label_lookup<67108864>(labels.get(),budget,1,n);check(loc.status==NativeLabelLookup::found,"trace lookup");v=labels[loc.slot];
#endif
 if(n==sink){check(v.cost==expected.cost&&v.hops==expected.hops,"sink cost");}
 if(v.parent==UINT32_MAX){break;}
 path.push_back(n);edges.push_back(v.edge);n=v.parent;}std::reverse(path.begin(),path.end());std::reverse(edges.begin(),edges.end());check(n==expected.attachment&&path==expected.path&&edges==expected.edges,"path mismatch");}
 std::cout<<"{\"status\":\"passed\",\"task\":"<<task<<",\"source\":"<<src<<",\"sink\":"<<sink<<",\"label_budget\":"<<budget<<",\"search_status\":"<<int(status)<<",\"expanded\":"<<expanded<<",\"edge_visits\":"<<visits<<",\"observations\":"<<used<<",\"csr_top_calls\":"<<csr_calls<<",\"raw_csr_visits\":"<<csr_scanned<<",\"scope\":\"Native CSR CPU component composition; unit hop cost, no live occupancy/owner transport or RTL claim\"}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
