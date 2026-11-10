#include "diagnostic.hpp"
#include <algorithm>
#include <chrono>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <tuple>
#include <filesystem>
using namespace persistroute;
using Clock=std::chrono::steady_clock;
uint64_t ns(Clock::time_point a){return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-a).count();}
namespace persistroute {
Observation observation;
bool observe_read(uint32_t id){++observation.calls;if(!observation.seen.at(id)){if(observation.ids.size()>=observation.limit){observation.failure="full_read_count_limit";return false;}observation.seen[id]=1;observation.ids.push_back(id);}return true;}
bool observe_push(MQEntry* q,uint32_t* sz,uint32_t depth,const MQEntry& e){bool ok=hbm_mq_push(q,sz,depth,e);uint64_t sum=0;for(unsigned i=0;i<MQ_QUEUES;++i)sum+=sz[i];observation.queue_peak=std::max(sum,observation.queue_peak);if(!ok)observation.failure="queue_capacity";return ok;}
}
template<class T>std::vector<T> load(const std::string& p){std::ifstream f(p,std::ios::binary|std::ios::ate);if(!f)throw std::runtime_error("missing "+p);auto n=f.tellg();if(n<0||size_t(n)%sizeof(T))throw std::runtime_error("ABI "+p);std::vector<T> v(size_t(n)/sizeof(T));f.seekg(0);f.read((char*)v.data(),n);if(!f)throw std::runtime_error("read "+p);return v;}
template<class T>void save(const std::string& p,const std::vector<T>& v){std::ofstream f(p,std::ios::binary);f.write((const char*)v.data(),v.size()*sizeof(T));if(!f)throw std::runtime_error("write "+p);}
uint64_t hashbytes(const void* p,size_t n){uint64_t h=14695981039346656037ULL;auto b=(const uint8_t*)p;while(n--){h^=*b++;h*=1099511628211ULL;}return h;}
template<class T>uint64_t hash(const std::vector<T>& v){return hashbytes(v.data(),v.size()*sizeof(T));}
bool equal(const std::vector<Resource>& a,const std::vector<Resource>& b){return a.size()==b.size()&&!std::memcmp(a.data(),b.data(),a.size()*sizeof(Resource));}
struct Answer {KernelCandidate c;std::vector<uint32_t> full;uint64_t reads=0,score_unique=0,peak=0,kernel_ns=0,total_ns=0;uint32_t cost=0;std::string reason="unknown";};
Answer search(const std::vector<Node>& nodes,const std::vector<Edge>& edges,const std::vector<Resource>& r,Task task,const std::vector<SearchSeed>& seeds,bool wide,uint32_t guard=0xffffffffU,uint32_t depth=0,uint32_t cap=0){
 auto begin=Clock::now();Answer a;a.c.task=task;uint32_t n=nodes.size();if(!depth)depth=std::max(256U,n);if(!cap)cap=n;
 std::vector<uint32_t> paths(cap),distance(n),pred(n),hops(n),seen(n),closed(n),re(n),sz(8);
 std::vector<ReadEntry> reads(cap);std::vector<MQEntry> q(size_t(8)*depth+seeds.size());
 task.epoch=seeds.size();task.reserved=size_t(8)*depth;
 for(size_t i=0;i<seeds.size();++i)q[task.reserved+i]={seeds[i].node,INVALID_RESOURCE,seeds[i].cost_q,seeds[i].hops};
 Metrics met{};PathResult small{};WideResult big{};
 if(wide)observation.reset(n,guard);
 auto k=Clock::now();
 if(wide)wide_search(nodes.data(),edges.data(),r.data(),&task,paths.data(),reads.data(),&big,distance.data(),pred.data(),hops.data(),seen.data(),closed.data(),re.data(),q.data(),sz.data(),n,edges.size(),1,depth,cap,&met);
 else search_hbm_kernel(nodes.data(),edges.data(),r.data(),&task,paths.data(),reads.data(),&small,distance.data(),pred.data(),hops.data(),seen.data(),closed.data(),re.data(),q.data(),sz.data(),n,edges.size(),1,depth,cap,&met);
 a.kernel_ns=ns(k);if(!wide)big={small.offset,small.length,small.status,small.read_offset,small.read_count,small.reserved};
 a.c.search_status=big.status;a.c.commit_status=big.status;
 if(big.status==1){a.c.path.assign(paths.begin()+big.offset,paths.begin()+big.offset+big.length);a.c.attachment=a.c.path.empty()?task.source:a.c.path.front();if(!seeds.empty()&&!a.c.path.empty())a.c.path.erase(a.c.path.begin());a.c.reads.assign(reads.begin()+big.read_offset,reads.begin()+big.read_offset+big.read_count);a.cost=distance.at(task.sink);}
 if(wide){a.full=observation.ids;a.reads=observation.score_calls;a.score_unique=observation.score_unique;a.peak=observation.queue_peak;a.reason=observation.failure;}else if(big.status==1)a.reason="none";
 a.total_ns=ns(begin);return a;
}
bool same(const Answer& a,const Answer& b){return a.c.search_status==b.c.search_status&&a.c.attachment==b.c.attachment&&a.c.path==b.c.path&&a.cost==b.cost;}
struct Commit {uint32_t status=0;uint64_t kernel_ns=0,total_ns=0;std::string reason="none";bool consistent=true;};
Commit commit(std::vector<Resource>& r,const KernelCandidate& c,bool allow,bool audit){
 auto begin=Clock::now();Commit z;auto before=audit?r:std::vector<Resource>{};auto b=audit?r:std::vector<Resource>{};auto d=b,e=b;
 if(c.path.size()>65535||c.reads.size()>65535){z.status=3;z.reason="production_record_capacity";return z;}
 size_t cap=std::max<size_t>({c.path.size(),c.reads.size(),1});auto path=c.path;auto read=c.reads;path.resize(cap);read.resize(cap);
 PathResult result{0,uint16_t(c.path.size()),c.search_status,0,uint16_t(c.reads.size()),0};Metrics m{};
 for(const auto& x:c.reads)if(x.resource_id>=r.size())z.reason="bounds";else if(!allow&&r[x.resource_id].owner!=c.task.net_id&&r[x.resource_id].version!=x.version)z.reason="version";
 for(auto id:c.path)if(id>=r.size())z.reason="bounds";else if(!allow&&r[id].owner!=c.task.net_id&&r[id].occupancy>=r[id].capacity&&z.reason=="none")z.reason="capacity";
 auto k=Clock::now();commit_hbm_kernel(r.data(),audit?b.data():r.data(),audit?d.data():r.data(),audit?e.data():r.data(),&c.task,path.data(),read.data(),&result,r.size(),1,cap,allow?1:0,&m);z.kernel_ns=ns(k);z.status=result.status;
 if(audit)z.consistent=equal(r,b)&&equal(r,d)&&equal(r,e)&&(z.status!=2||equal(r,before));z.total_ns=ns(begin);return z;
}
bool validate_full(const Answer& a,const std::vector<Resource>& old,const std::vector<Resource>& now,uint32_t& differences){differences=0;for(auto id:a.full)if(std::memcmp(&old[id],&now[id],sizeof(Resource)))++differences;return differences==0;}
bool structural(const Answer& a,const std::vector<Node>& nodes,const std::vector<Edge>& edges,const std::vector<SearchSeed>& seeds){if(a.c.search_status!=1)return false;bool seed=false;for(auto s:seeds)seed|=s.node==a.c.attachment;if(!seed)return false;uint32_t p=a.c.attachment;std::vector<uint32_t> visited{p};for(auto id:a.c.path){if(id>=nodes.size()||std::find(visited.begin(),visited.end(),id)!=visited.end())return false;bool edge=false;for(uint32_t j=0;j<nodes[p].edge_count;++j)edge|=edges[nodes[p].edge_begin+j].dst==id;if(!edge)return false;for(auto s:seeds)if(id==s.node)return false;visited.push_back(id);p=id;}return p==a.c.task.sink;}
struct SampleDone{};
void capture(const std::string& prefix,const std::string& out){
 auto nodes=load<Node>(prefix+".nodes");auto edges=load<Edge>(prefix+".edges");auto initial=load<Resource>(prefix+".resources");auto tasks=load<Task>(prefix+".tasks");
 std::filesystem::create_directories(out);std::ofstream csv(out+"/replay.csv");csv<<"query,iteration,wave,batch,order,task,net,source,sink,criticality,task_epoch,seeds,state_fnv64,tree_fnv64,mode,allow_overuse,search_status,commit_status,reason,read_unique,logical_record_bytes,score_unique,resource_load_calls,path_length,queue_peak,dependency_changes,full_valid,path_diff_S,cost_diff_S,repeat_equal,structural_ok,state_consistent,search_kernel_ns,search_total_ns,validate_ns,commit_kernel_ns\n";
 unsigned count=0,batches=0;bool inconsistent=false;
 KernelBatchExecutor executor=[&](const auto& n,const auto& e,auto& resources,const auto& ts,const auto& seedlists,bool allow){
  if(count>=16)throw SampleDone{};auto before=resources;auto batch=execute_hbm_cmodel_batch(n,e,resources,ts,seedlists,allow,4,0,0);auto current=before;
  save(out+"/batch"+std::to_string(batches)+".resources",before);unsigned order=0;
  for(const auto& c:batch.candidates){auto it=std::find_if(ts.begin(),ts.end(),[&](const auto& t){return t.id==c.task.id;});size_t index=it-ts.begin();const auto& task=*it;const auto& seeds=seedlists[index];
   if(count<16){std::string stem=out+"/q"+std::to_string(count);save(stem+".resources",current);save(stem+".task",std::vector<Task>{task});save(stem+".seeds",seeds);save(stem+".batch",std::vector<uint32_t>{batches});
    auto wide=search(n,e,before,task,seeds,true);auto narrow=search(n,e,before,task,seeds,false);auto serial=search(n,e,current,task,seeds,false);auto repeat=search(n,e,before,task,seeds,true);
    bool match=same(wide,narrow)&&wide.c.path==c.path&&wide.c.attachment==c.attachment&&wide.c.search_status==c.search_status;
    bool deterministic=same(wide,repeat);bool structure=structural(wide,n,e,seeds);if(!match||!deterministic||(wide.c.search_status==1&&!structure))inconsistent=true;
    uint32_t changes=0;auto vb=Clock::now();bool valid=validate_full(wide,before,current,changes);auto vn=ns(vb);
    for(char mode:std::string("SFPN")){auto state=current;const auto& answer=(mode=='S'||(mode=='F'&&!valid))?serial:wide;auto cc=commit(state,answer.c,mode=='P'?false:allow,true);inconsistent|=!cc.consistent;
     csv<<count<<",0,1,"<<batches<<','<<order<<','<<task.id<<','<<task.net_id<<','<<task.source<<','<<task.sink<<','<<task.criticality_q<<','<<task.epoch<<','<<seeds.size()<<','<<hash(current)<<','<<hash(seeds)<<','<<mode<<','<<(mode=='P'?0:allow)<<','<<answer.c.search_status<<','<<cc.status<<','<<cc.reason<<','<<(mode=='F'?wide.full.size():answer.c.reads.size())<<','<<(mode=='F'?wide.full.size()*20:answer.c.reads.size()*8)<<','<<wide.score_unique<<','<<wide.reads<<','<<answer.c.path.size()<<','<<wide.peak<<','<<changes<<','<<valid<<','<<(answer.c.path!=serial.c.path||answer.c.attachment!=serial.c.attachment)<<','<<(answer.cost!=serial.cost)<<','<<deterministic<<','<<structure<<','<<(cc.consistent&&match)<<','<<answer.kernel_ns<<','<<answer.total_ns<<','<<(mode=='F'?vn:0)<<','<<cc.kernel_ns<<'\n';
    }
    ++count;
   }
   auto cc=commit(current,c,allow,true);if(cc.status!=c.commit_status||!cc.consistent)inconsistent=true;++order;
  }
  if(!equal(current,resources))inconsistent=true;++batches;csv.flush();if(inconsistent)throw std::runtime_error("correctness mismatch: stop performance");return batch;
 };
 PathfinderConfig config;config.max_iterations=1;config.min_timing_iterations=1;config.route_tree_timing_weight_q=0;
 try{route_accelerated_pathfinder(nodes,edges,initial,tasks,executor,config,8);}catch(SampleDone&){}
 std::ofstream s(out+"/capture_status.json");s<<"{\"status\":\"partial_fixed_sample\",\"queries\":"<<count<<",\"batches\":"<<batches<<",\"final_legality\":\"unknown\",\"state_consistent\":"<<(!inconsistent?"true":"false")<<"}\n";
}
void performance(const std::string& prefix,const std::string& out){
 auto nodes=load<Node>(prefix+".nodes");auto edges=load<Edge>(prefix+".edges");std::ofstream csv(out+"/performance.csv");csv<<"query,mode,search_total_ns,search_kernel_ns,validation_ns,commit_total_ns,commit_kernel_ns,replayed,status\n";
 for(unsigned i=0;i<16;++i){auto stem=out+"/q"+std::to_string(i);if(!std::filesystem::exists(stem+".task"))break;auto task=load<Task>(stem+".task")[0];auto seeds=load<SearchSeed>(stem+".seeds");auto now=load<Resource>(stem+".resources");auto batch=load<uint32_t>(stem+".batch")[0];auto old=load<Resource>(out+"/batch"+std::to_string(batch)+".resources");
  for(char mode:std::string("SFPN")){auto a=search(nodes,edges,mode=='S'?now:old,task,seeds,mode=='F');uint64_t total=a.total_ns,kernel=a.kernel_ns,vtime=0;bool replay=false;
   if(mode=='F'){uint32_t changes;auto b=Clock::now();bool valid=validate_full(a,old,now,changes);vtime=ns(b);if(!valid){replay=true;a=search(nodes,edges,now,task,seeds,false);total+=a.total_ns;kernel+=a.kernel_ns;}}
   auto state=now;auto cc=commit(state,a.c,mode!='P',false);csv<<i<<','<<mode<<','<<total<<','<<kernel<<','<<vtime<<','<<cc.total_ns<<','<<cc.kernel_ns<<','<<replay<<','<<cc.status<<'\n';
  }
 }
}
struct Graph{std::vector<Node> n;std::vector<Edge> e;std::vector<Resource> r;Graph(unsigned count):n(count),r(count){for(auto& x:r){x.capacity=1;x.owner=INVALID_RESOURCE;}}void set(unsigned u,const std::vector<Edge>& es){n[u]={uint32_t(e.size()),uint16_t(es.size()),0};e.insert(e.end(),es.begin(),es.end());}};
Task task_for(unsigned sink){return Task{1,7,0,sink,0,65535,0,0,0};}
void synthetic(const std::string& out){std::filesystem::create_directories(out);std::ofstream f(out+"/witnesses.csv");f<<"id,old_status,current_status,old_path_fnv,current_path_fnv,old_cost,current_cost,full_reads,queue_peak,F_valid,P_status,N_status,PN_state_consistent,note\n";
 auto witness=[&](std::string id,Graph& g,std::vector<Resource> current,Task task,std::vector<SearchSeed> seeds,std::vector<SearchSeed> newseeds,std::string note){auto old=search(g.n,g.e,g.r,task,seeds,true);auto now=search(g.n,g.e,current,task,newseeds,true);uint32_t diff;bool valid=validate_full(old,g.r,current,diff)&&hash(seeds)==hash(newseeds);auto pstate=current,nstate=current;auto p=commit(pstate,old.c,false,true),n=commit(nstate,old.c,true,true);f<<id<<','<<old.c.search_status<<','<<now.c.search_status<<','<<hash(old.c.path)<<','<<hash(now.c.path)<<','<<old.cost<<','<<now.cost<<','<<old.full.size()<<','<<old.peak<<','<<valid<<','<<p.status<<','<<n.status<<','<<(p.consistent&&n.consistent)<<','<<note<<'\n';};
 Graph diamond(4);diamond.set(0,{{1,1,0},{2,1,0}});diamond.set(1,{{3,1,0}});diamond.set(2,{{3,1,0}});diamond.r[1].history_cost_q=3;diamond.r[2].history_cost_q=9;auto t=task_for(3);std::vector<SearchSeed> seed{{0,0,0}};auto current=diamond.r;current[2].history_cost_q=0;++current[2].version;witness("off_path_decrease",diamond,current,t,seed,seed,"legal_stale_path_fresh_optimum_changes");
 current=diamond.r;current[2].history_cost_q=20;++current[2].version;witness("off_path_increase",diamond,current,t,seed,seed,"F_rejects_but_same_path");
 current=diamond.r;++current[1].version;witness("on_path_version",diamond,current,t,seed,seed,"P_rejects_N_accepts");
 current=diamond.r;current[1].occupancy=1;current[1].owner=9;++current[1].version;witness("other_net_full",diamond,current,t,seed,seed,"negotiated_intermediate_overuse_not_final_illegality");
 current=diamond.r;current[1].occupancy=1;current[1].owner=7;++current[1].version;witness("same_net_owned",diamond,current,t,seed,seed,"P_bypasses_version_same_net_no_increment");
 auto rip=diamond;rip.r[2].occupancy=1;rip.r[2].owner=9;rip.r[2].present_cost_q=20;current=rip.r;current[2].occupancy=0;current[2].history_cost_q=0;current[2].owner=INVALID_RESOURCE;++current[2].version;witness("ripup_decrease",rip,current,t,seed,seed,"modeled_event_not_historical_trace");
 current=diamond.r;current[1].owner=7;current[1].occupancy=1;witness("tree_seed_change",diamond,current,t,seed,{{1,1,0}},"resource_versions_alone_do_not_bind_tree");
 Graph chain(3);chain.set(0,{{1,1,0}});chain.set(1,{{2,1,0}});auto a=search(chain.n,chain.e,chain.r,task_for(2),seed,true);auto state=chain.r;auto first=commit(state,a.c,false,true);auto second=commit(state,a.c,false,true);f<<"same_net_repeat,1,1,0,0,2,2,2,1,0,"<<second.status<<','<<second.status<<','<<second.consistent<<",occupancy_trunk="<<state[1].occupancy<<";same_owner_bypass\n";
 current=chain.r;current[1].occupancy=65535;current[1].version=0xffffffffU;auto sat=commit(current,a.c,true,true);f<<"integer_commit_boundary,1,1,0,0,0,0,2,1,0,0,"<<sat.status<<','<<sat.consistent<<",occupancy="<<current[1].occupancy<<";version="<<current[1].version<<";outside_valid_unique_owner_range\n";
 auto invalid=a.c;invalid.path.push_back(100);current=chain.r;auto rollback=commit(current,invalid,true,true);f<<"failed_rollback,1,1,0,0,0,0,2,1,0,0,"<<rollback.status<<','<<(rollback.consistent&&equal(current,chain.r))<<",out_of_bounds_last_path_no_partial_writes\n";
 auto high=search(chain.n,chain.e,chain.r,task_for(2),{{0,0,0xfffffffeU}},true);f<<"cost_saturation,"<<high.c.search_status<<",1,0,0,"<<high.cost<<",4294967295,"<<high.full.size()<<','<<high.peak<<",1,0,0,1,uint64_intermediate_uint32_saturation\n";
 auto small=search(chain.n,chain.e,chain.r,task_for(2),seed,false,0xffffffffU,256,1);f<<"path_pool_boundary,"<<small.c.search_status<<",1,0,0,0,0,0,0,0,0,0,1,one_entry_capacity_insufficient\n";
 Graph fan(65538);std::vector<Edge> list;for(unsigned i=1;i<=65535;++i)list.push_back({i,1,0});fan.set(0,list);fan.set(1,{{65536,1,0}});fan.set(65536,{{65537,100,0}});auto ft=task_for(65537);auto wide=search(fan.n,fan.e,fan.r,ft,seed,true);auto guard=search(fan.n,fan.e,fan.r,ft,seed,true,65535);auto queue=search(fan.n,fan.e,fan.r,ft,seed,true,0xffffffffU,1);
 f<<"full_read_boundary,"<<guard.c.search_status<<','<<wide.c.search_status<<",0,0,0,"<<wide.cost<<','<<wide.full.size()<<','<<wide.peak<<",0,0,0,1,"<<guard.reason<<"\n";
 f<<"queue_boundary,"<<queue.c.search_status<<','<<wide.c.search_status<<",0,0,0,0,"<<queue.full.size()<<','<<queue.peak<<",0,0,0,1,"<<queue.reason<<"\n";
 Graph longpath(65536);for(unsigned i=0;i<65535;++i)longpath.set(i,{{i+1,1,0}});auto lt=task_for(65535);auto lw=search(longpath.n,longpath.e,longpath.r,lt,seed,true);auto ln=search(longpath.n,longpath.e,longpath.r,lt,seed,false);f<<"path_count_boundary,"<<ln.c.search_status<<','<<lw.c.search_status<<",0,0,0,"<<lw.cost<<','<<lw.full.size()<<','<<lw.peak<<",0,0,0,1,65536_path_entries_including_attachment\n";
 Graph disconnected(2);auto u=search(disconnected.n,disconnected.e,disconnected.r,task_for(1),seed,true);f<<"unreachable_known_graph,"<<u.c.search_status<<",3,0,0,0,0,0,"<<u.peak<<",0,0,0,1,"<<u.reason<<"\n";
}
int main(int argc,char** argv){try{if(argc==3&&std::string(argv[1])=="synthetic")synthetic(argv[2]);else if(argc==4&&std::string(argv[1])=="capture")capture(argv[2],argv[3]);else if(argc==4&&std::string(argv[1])=="performance")performance(argv[2],argv[3]);else throw std::runtime_error("usage: pr0 synthetic out | capture/performance prefix out");return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}}
