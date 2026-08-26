#include "persistroute.hpp"
#include "multiqueue.hpp"

#include <xrt/xrt_bo.h>
#include <xrt/xrt_device.h>
#include <xrt/xrt_kernel.h>

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

using namespace persistroute;
static_assert(sizeof(Node)==8&&sizeof(Edge)==8&&sizeof(Resource)==16&&sizeof(Task)==32&&sizeof(ReadEntry)==8&&sizeof(PathResult)==16,"host/kernel ABI mismatch");

template<typename T>std::vector<T> read_array(const std::string&path){std::ifstream in(path,std::ios::binary|std::ios::ate);if(!in)throw std::runtime_error("cannot open "+path);const auto bytes=static_cast<std::size_t>(in.tellg());if(bytes%sizeof(T))throw std::runtime_error("misaligned "+path);std::vector<T> out(bytes/sizeof(T));in.seekg(0);in.read(reinterpret_cast<char*>(out.data()),static_cast<std::streamsize>(bytes));return out;}
template<typename T>void upload(xrt::bo&bo,const std::vector<T>&v){if(v.empty())return;std::memcpy(bo.map<void*>(),v.data(),v.size()*sizeof(T));bo.sync(XCL_BO_SYNC_BO_TO_DEVICE, v.size()*sizeof(T),0);}
template<typename T>void download(xrt::bo&bo,std::vector<T>&v){if(v.empty())return;bo.sync(XCL_BO_SYNC_BO_FROM_DEVICE,v.size()*sizeof(T),0);std::memcpy(v.data(),bo.map<void*>(),v.size()*sizeof(T));}
std::uint32_t env_u32(const char*name,std::uint32_t fallback){const char*value=std::getenv(name);if(!value)return fallback;const unsigned long parsed=std::stoul(value);if(parsed==0||parsed>0xffffffffUL)throw std::runtime_error(std::string("bad ")+name);return static_cast<std::uint32_t>(parsed);}

struct PE {
 std::unique_ptr<xrt::kernel> kernel;std::unique_ptr<xrt::bo> nodes,edges,resources,tasks,paths,reads,results,distance,predecessor,hops,seen,closed,read_epoch,queue,sizes,metrics;
 std::vector<Task> host_tasks;std::vector<std::uint32_t> host_paths;std::vector<ReadEntry> host_reads;std::vector<PathResult> host_results;
};
struct Candidate{Task task;PathResult result;std::vector<std::uint32_t> path;std::vector<ReadEntry> reads;};

int main(int argc,char**argv){try{
 if(argc!=4){std::cerr<<"usage: persistroute_multi_xrt <xclbin> <input-prefix> <output-prefix>\n";return 2;}
 const auto process_begin=std::chrono::steady_clock::now();const std::string xclbin=argv[1],input=argv[2],output=argv[3];auto nodes=read_array<Node>(input+".nodes");auto edges=read_array<Edge>(input+".edges");auto resources=read_array<Resource>(input+".resources");auto all_tasks=read_array<Task>(input+".tasks");const auto input_end=std::chrono::steady_clock::now();
 if(nodes.empty()||resources.size()!=nodes.size()||all_tasks.empty())throw std::runtime_error("empty graph/tasks or resource count mismatch");
 std::sort(all_tasks.begin(),all_tasks.end(),[](const Task&a,const Task&b){return a.priority<b.priority||(a.priority==b.priority&&a.id<b.id);});
 const std::uint32_t pe_count=std::min<std::uint32_t>(env_u32("PERSISTROUTE_PE_COUNT",4),static_cast<std::uint32_t>(all_tasks.size()));const std::uint32_t max_rounds=env_u32("PERSISTROUTE_MAX_REPLAY",8);
 const std::uint32_t queue_depth=env_u32("PERSISTROUTE_QUEUE_DEPTH",std::max<std::uint32_t>(256,(2*nodes.size()+MQ_QUEUES-1)/MQ_QUEUES));
 const std::uint32_t tx_capacity=env_u32("PERSISTROUTE_TX_CAPACITY",std::max<std::uint32_t>(4096,static_cast<std::uint32_t>((all_tasks.size()+pe_count-1)/pe_count)*std::min<std::uint32_t>(static_cast<std::uint32_t>(nodes.size()),1024)));
 xrt::device device(0);const auto uuid=device.load_xclbin(xclbin);xrt::kernel commit(device,uuid,"commit_hbm_kernel:{commit_hbm_kernel_1}");
 auto bo_resources=std::make_unique<xrt::bo>(device,resources.size()*sizeof(Resource),commit.group_id(0));upload(*bo_resources,resources);
 const std::uint32_t max_tasks_per_pe=(static_cast<std::uint32_t>(all_tasks.size())+pe_count-1)/pe_count;std::vector<PE> pes(pe_count);
 for(std::uint32_t i=0;i<pe_count;++i){PE&pe=pes[i];const std::string name="search_hbm_kernel:{search_hbm_kernel_"+std::to_string(i+1)+"}";pe.kernel=std::make_unique<xrt::kernel>(device,uuid,name);auto make=[&](std::size_t bytes,int arg){return std::make_unique<xrt::bo>(device,std::max<std::size_t>(bytes,64),pe.kernel->group_id(arg));};
  pe.nodes=make(nodes.size()*sizeof(Node),0);pe.edges=make(edges.size()*sizeof(Edge),1);pe.resources=make(resources.size()*sizeof(Resource),2);pe.tasks=make(max_tasks_per_pe*sizeof(Task),3);pe.paths=make(tx_capacity*sizeof(std::uint32_t),4);pe.reads=make(tx_capacity*sizeof(ReadEntry),5);pe.results=make(max_tasks_per_pe*sizeof(PathResult),6);pe.distance=make(nodes.size()*sizeof(std::uint32_t),7);pe.predecessor=make(nodes.size()*sizeof(std::uint32_t),8);pe.hops=make(nodes.size()*sizeof(std::uint32_t),9);pe.seen=make(nodes.size()*sizeof(std::uint32_t),10);pe.closed=make(nodes.size()*sizeof(std::uint32_t),11);pe.read_epoch=make(nodes.size()*sizeof(std::uint32_t),12);pe.queue=make(static_cast<std::size_t>(MQ_QUEUES)*queue_depth*sizeof(MQEntry),13);pe.sizes=make(MQ_QUEUES*sizeof(std::uint32_t),14);pe.metrics=make(sizeof(Metrics),20);upload(*pe.nodes,nodes);upload(*pe.edges,edges);pe.host_paths.resize(tx_capacity);pe.host_reads.resize(tx_capacity);
 }
 std::vector<Task> pending=all_tasks;std::map<std::uint32_t,std::vector<std::uint32_t>> committed_paths;std::uint64_t conflict_total=0,failed_total=0;const auto setup_end=std::chrono::steady_clock::now();
 for(std::uint32_t round=0;round<max_rounds&&!pending.empty();++round){download(*bo_resources,resources);for(auto&pe:pes)pe.host_tasks.clear();for(std::size_t i=0;i<pending.size();++i){Task task=pending[i];task.epoch=round;pes[i%pe_count].host_tasks.push_back(task);}std::vector<xrt::run> runs;runs.reserve(pe_count);
  for(auto&pe:pes){pe.host_results.assign(pe.host_tasks.size(),PathResult{});upload(*pe.resources,resources);upload(*pe.tasks,pe.host_tasks);runs.push_back((*pe.kernel)(*pe.nodes,*pe.edges,*pe.resources,*pe.tasks,*pe.paths,*pe.reads,*pe.results,*pe.distance,*pe.predecessor,*pe.hops,*pe.seen,*pe.closed,*pe.read_epoch,*pe.queue,*pe.sizes,static_cast<std::uint32_t>(nodes.size()),static_cast<std::uint32_t>(edges.size()),static_cast<std::uint32_t>(pe.host_tasks.size()),queue_depth,tx_capacity,*pe.metrics));}
	  for(auto&run:runs)run.wait();
	  std::vector<Candidate> candidates;
  for(auto&pe:pes){download(*pe.results,pe.host_results);download(*pe.paths,pe.host_paths);download(*pe.reads,pe.host_reads);for(std::size_t i=0;i<pe.host_tasks.size();++i){const PathResult r=pe.host_results[i];Candidate c{pe.host_tasks[i],r,{},{}};if(r.status==1&&r.offset+r.length<=pe.host_paths.size()&&r.read_offset+r.read_count<=pe.host_reads.size()){c.path.assign(pe.host_paths.begin()+r.offset,pe.host_paths.begin()+r.offset+r.length);c.reads.assign(pe.host_reads.begin()+r.read_offset,pe.host_reads.begin()+r.read_offset+r.read_count);}candidates.push_back(std::move(c));}}
  std::sort(candidates.begin(),candidates.end(),[](const Candidate&a,const Candidate&b){return a.task.priority<b.task.priority||(a.task.priority==b.task.priority&&a.task.id<b.task.id);});std::vector<Task> commit_tasks;std::vector<std::uint32_t> commit_paths;std::vector<ReadEntry> commit_reads;std::vector<PathResult> commit_results;
  for(auto&c:candidates){PathResult r=c.result;r.offset=static_cast<std::uint32_t>(commit_paths.size());r.read_offset=static_cast<std::uint32_t>(commit_reads.size());if(r.status==1){commit_paths.insert(commit_paths.end(),c.path.begin(),c.path.end());commit_reads.insert(commit_reads.end(),c.reads.begin(),c.reads.end());}commit_tasks.push_back(c.task);commit_results.push_back(r);}
  const std::uint32_t commit_capacity=static_cast<std::uint32_t>(std::max(commit_paths.size(),commit_reads.size()));auto make_commit=[&](std::size_t bytes,int arg){return xrt::bo(device,std::max<std::size_t>(bytes,64),commit.group_id(arg));};auto bo_tasks=make_commit(commit_tasks.size()*sizeof(Task),1);auto bo_paths=make_commit(std::max<std::size_t>(commit_paths.size(),1)*sizeof(std::uint32_t),2);auto bo_reads=make_commit(std::max<std::size_t>(commit_reads.size(),1)*sizeof(ReadEntry),3);auto bo_results=make_commit(commit_results.size()*sizeof(PathResult),4);auto bo_metrics=make_commit(sizeof(Metrics),9);upload(bo_tasks,commit_tasks);upload(bo_paths,commit_paths);upload(bo_reads,commit_reads);upload(bo_results,commit_results);auto commit_run=commit(*bo_resources,bo_tasks,bo_paths,bo_reads,bo_results,static_cast<std::uint32_t>(resources.size()),static_cast<std::uint32_t>(commit_tasks.size()),commit_capacity,0U,bo_metrics);commit_run.wait();download(bo_results,commit_results);
  std::vector<Task> replay;std::uint32_t progress=0;for(std::size_t i=0;i<commit_results.size();++i){const auto status=commit_results[i].status;if(status==4){committed_paths[commit_tasks[i].id]=candidates[i].path;++progress;}else if(status==2){replay.push_back(commit_tasks[i]);++conflict_total;}else ++failed_total;}if(progress==0&&!replay.empty())throw std::runtime_error("replay made no progress; increase capacity or inspect congestion");pending.swap(replay);
 }
 const auto route_end=std::chrono::steady_clock::now();download(*bo_resources,resources);std::ofstream route_out(output+".paths.csv");route_out<<"task_id,path_index,resource_id\n";for(const auto&entry:committed_paths)for(std::size_t i=0;i<entry.second.size();++i)route_out<<entry.first<<','<<i<<','<<entry.second[i]<<'\n';route_out.close();std::ofstream state_out(output+".resources",std::ios::binary);state_out.write(reinterpret_cast<const char*>(resources.data()),static_cast<std::streamsize>(resources.size()*sizeof(Resource)));state_out.close();const auto output_end=std::chrono::steady_clock::now();auto ms=[](auto a,auto b){return std::chrono::duration<double,std::milli>(b-a).count();};std::cout<<"{\"wall_ms\":"<<ms(process_begin,output_end)<<",\"input_ms\":"<<ms(process_begin,input_end)<<",\"setup_ms\":"<<ms(input_end,setup_end)<<",\"route_replay_ms\":"<<ms(setup_end,route_end)<<",\"output_ms\":"<<ms(route_end,output_end)<<",\"pes\":"<<pe_count<<",\"tasks\":"<<all_tasks.size()<<",\"committed\":"<<committed_paths.size()<<",\"remaining\":"<<pending.size()<<",\"conflicts\":"<<conflict_total<<",\"failed\":"<<failed_total<<"}\n";return pending.empty()&&failed_total==0?0:3;
 }catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<'\n';return 1;}}
