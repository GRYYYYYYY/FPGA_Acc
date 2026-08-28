#include "accelerated_pathfinder.hpp"
#include "external_timing.hpp"
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
#include <iomanip>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

using namespace persistroute;
static_assert(sizeof(Node)==8&&sizeof(Edge)==8&&sizeof(Resource)==16&&sizeof(Task)==32&&sizeof(PathResult)==16,"host/kernel ABI mismatch");

template<typename T>std::vector<T> read_array(const std::string& path){std::ifstream in(path,std::ios::binary|std::ios::ate);if(!in)throw std::runtime_error("cannot open "+path);const auto end=in.tellg();if(end<0||static_cast<std::uint64_t>(end)%sizeof(T))throw std::runtime_error("misaligned "+path);std::vector<T> out(static_cast<std::size_t>(end)/sizeof(T));in.seekg(0);if(!out.empty())in.read(reinterpret_cast<char*>(out.data()),out.size()*sizeof(T));if(!in)throw std::runtime_error("cannot read "+path);return out;}
template<typename T>void write_array(const std::string& path,const std::vector<T>& data){std::ofstream out(path,std::ios::binary);if(!out)throw std::runtime_error("cannot create "+path);if(!data.empty())out.write(reinterpret_cast<const char*>(data.data()),data.size()*sizeof(T));if(!out)throw std::runtime_error("cannot write "+path);}
template<typename T>void upload(xrt::bo& bo,const std::vector<T>& data,std::size_t offset=0){if(data.empty())return;std::memcpy(static_cast<unsigned char*>(bo.map<void*>())+offset,data.data(),data.size()*sizeof(T));bo.sync(XCL_BO_SYNC_BO_TO_DEVICE,data.size()*sizeof(T),offset);}
template<typename T>void download(xrt::bo& bo,std::vector<T>& data,std::size_t offset=0){if(data.empty())return;bo.sync(XCL_BO_SYNC_BO_FROM_DEVICE,data.size()*sizeof(T),offset);std::memcpy(data.data(),static_cast<unsigned char*>(bo.map<void*>())+offset,data.size()*sizeof(T));}
std::uint32_t env_u32(const char* name,std::uint32_t fallback){const char* text=std::getenv(name);if(!text)return fallback;std::size_t used=0;const unsigned long value=std::stoul(text,&used,0);if(text[used]||value>0xffffffffUL)throw std::runtime_error(std::string("bad ")+name);return value;}
std::uint16_t env_u16(const char* name,std::uint16_t fallback){const auto value=env_u32(name,fallback);if(value>65535U)throw std::runtime_error(std::string("bad ")+name);return value;}
std::string slurp(const std::string& path){std::ifstream in(path,std::ios::binary);if(!in)return {};return std::string(std::istreambuf_iterator<char>(in),{});}

struct SearchPe {std::unique_ptr<xrt::kernel> kernel;std::unique_ptr<xrt::bo> nodes,edges,resources,tasks,path,reads,results,distance,predecessor,hops,seen,closed,read_epoch,queue,sizes,metrics;};

class XrtExecutor {
public:
 XrtExecutor(const std::string& xclbin,const std::vector<Node>& nodes,const std::vector<Edge>& edges,
             std::uint32_t pe_count,std::uint32_t queue_depth,std::uint32_t tasks_per_cu,
             std::uint32_t transaction_capacity)
     : nodes_(nodes),edges_(edges),pe_count_(pe_count),
       queue_depth_(queue_depth?queue_depth:std::max<std::uint32_t>(256,(8ULL*nodes.size()+MQ_QUEUES-1)/MQ_QUEUES)),
       tasks_per_cu_(tasks_per_cu),active_queue_(static_cast<std::size_t>(MQ_QUEUES)*queue_depth_),
       tx_capacity_(transaction_capacity?transaction_capacity:std::max<std::size_t>(nodes.size()+1,static_cast<std::size_t>(tasks_per_cu)*65536ULL)),
       batch_capacity_(static_cast<std::size_t>(pe_count)*tasks_per_cu),device_(0),
       uuid_(device_.load_xclbin(xclbin)),commit_(device_,uuid_,"commit_hbm_kernel:{commit_hbm_kernel_1}") {
  if(pe_count_==0||pe_count_>4||nodes_.empty()||tasks_per_cu_==0||tx_capacity_>0xffffffffULL)
   throw std::invalid_argument("XRT PE count/graph/batch is invalid");
  auto commit_bo=[&](std::size_t bytes,int arg){return std::make_unique<xrt::bo>(device_,std::max<std::size_t>(bytes,64),commit_.group_id(arg));};
  commit_tasks_=commit_bo(batch_capacity_*sizeof(Task),4);
  commit_paths_=commit_bo(4*tx_capacity_*sizeof(std::uint32_t),5);
  commit_reads_=commit_bo(4*tx_capacity_*sizeof(ReadEntry),6);
  commit_results_=commit_bo(batch_capacity_*sizeof(PathResult),7);
  commit_metrics_=commit_bo(sizeof(Metrics),12);
  pes_.resize(4);
  for(std::uint32_t i=0;i<4;++i){
   auto& pe=pes_[i];pe.kernel=std::make_unique<xrt::kernel>(device_,uuid_,"search_hbm_kernel:{search_hbm_kernel_"+std::to_string(i+1)+"}");
   auto make=[&](std::size_t bytes,int arg){return std::make_unique<xrt::bo>(device_,std::max<std::size_t>(bytes,64),pe.kernel->group_id(arg));};
   pe.nodes=make(nodes.size()*sizeof(Node),0);pe.edges=make(edges.size()*sizeof(Edge),1);
   pe.resources=make(nodes.size()*sizeof(Resource),2);pe.tasks=make(tasks_per_cu_*sizeof(Task),3);
   pe.path=make(tx_capacity_*sizeof(std::uint32_t),4);pe.reads=make(tx_capacity_*sizeof(ReadEntry),5);
   pe.results=make(tasks_per_cu_*sizeof(PathResult),6);pe.distance=make(nodes.size()*sizeof(std::uint32_t),7);
   pe.predecessor=make(nodes.size()*sizeof(std::uint32_t),8);pe.hops=make(nodes.size()*sizeof(std::uint32_t),9);
   pe.seen=make(nodes.size()*sizeof(std::uint32_t),10);pe.closed=make(nodes.size()*sizeof(std::uint32_t),11);
   pe.read_epoch=make(nodes.size()*sizeof(std::uint32_t),12);pe.queue=make((active_queue_+tx_capacity_)*sizeof(MQEntry),13);
   pe.sizes=make(MQ_QUEUES*sizeof(std::uint32_t),14);pe.metrics=make(sizeof(Metrics),20);
   upload(*pe.nodes,nodes_);upload(*pe.edges,edges_);
  }
  setup_h2d_bytes_=4ULL*(nodes_.size()*sizeof(Node)+edges_.size()*sizeof(Edge));
 }

 KernelBatchResult operator()(const std::vector<Node>&,const std::vector<Edge>&,
                              std::vector<Resource>& resources,const std::vector<Task>& tasks,
                              const std::vector<std::vector<SearchSeed>>& seeds,bool allow_overuse){
  if(tasks.size()!=seeds.size()||tasks.size()>batch_capacity_)
   throw std::invalid_argument("XRT batch exceeds configured capacity");
  KernelBatchResult output;if(tasks.empty())return output;
  output.telemetry.h2d_bytes+=setup_h2d_bytes_;setup_h2d_bytes_=0;sync_resources(resources,output.telemetry);
  std::vector<std::vector<std::size_t>> partitions(pe_count_);
  for(std::size_t i=0;i<tasks.size();++i)partitions[i%pe_count_].push_back(i);
  std::vector<xrt::run> runs;runs.reserve(pe_count_);const auto search_begin=std::chrono::steady_clock::now();
  for(std::size_t i=0;i<partitions.size();++i){
   if(partitions[i].empty())continue;
   auto& pe=pes_[i];std::vector<Task> part;std::vector<MQEntry> seed_entries;
   part.reserve(partitions[i].size());
   for(const auto index:partitions[i]){
    if(seeds[index].empty()||seeds[index].size()>nodes_.size()||seed_entries.size()+seeds[index].size()>tx_capacity_)
     throw std::runtime_error("invalid XRT seed list");
    Task task=tasks[index];task.epoch=seeds[index].size();task.reserved=active_queue_+seed_entries.size();part.push_back(task);
    for(const auto& seed:seeds[index])seed_entries.push_back({seed.node,INVALID_RESOURCE,0,seed.hops});
   }
   upload(*pe.tasks,part);upload(*pe.queue,seed_entries,active_queue_*sizeof(MQEntry));
   output.telemetry.h2d_bytes+=part.size()*sizeof(Task)+seed_entries.size()*sizeof(MQEntry);
   runs.push_back((*pe.kernel)(*pe.nodes,*pe.edges,*pe.resources,*pe.tasks,*pe.path,*pe.reads,*pe.results,
    *pe.distance,*pe.predecessor,*pe.hops,*pe.seen,*pe.closed,*pe.read_epoch,*pe.queue,*pe.sizes,
    nodes_.size(),edges_.size(),part.size(),queue_depth_,tx_capacity_,*pe.metrics));
   ++output.telemetry.search_launches;
  }
  for(auto& run:runs)run.wait();
  output.telemetry.search_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-search_begin).count();
  for(std::size_t i=0;i<partitions.size();++i){
   if(partitions[i].empty())continue;
   auto& pe=pes_[i];std::vector<PathResult> part_results(partitions[i].size());std::vector<Metrics> metric(1);
   download(*pe.results,part_results);download(*pe.metrics,metric);
   output.telemetry.d2h_bytes+=part_results.size()*sizeof(PathResult)+sizeof(Metrics);
   output.search_metrics.expanded+=metric[0].expanded;output.search_metrics.edge_visits+=metric[0].edge_visits;output.search_metrics.failed+=metric[0].failed;
   for(std::size_t j=0;j<partitions[i].size();++j){
    const auto index=partitions[i][j];const auto& result=part_results[j];KernelCandidate candidate{};
    candidate.task=tasks[index];candidate.search_status=result.status;candidate.commit_status=result.status;
    if(result.status==1){
     std::vector<std::uint32_t> raw(result.length);std::vector<ReadEntry> read(result.read_count);
     download(*pe.path,raw,result.offset*sizeof(std::uint32_t));download(*pe.reads,read,result.read_offset*sizeof(ReadEntry));
     output.telemetry.d2h_bytes+=raw.size()*sizeof(std::uint32_t)+read.size()*sizeof(ReadEntry);
     if(raw.empty())throw std::runtime_error("XRT multi-source result omitted attachment");
     candidate.attachment=raw.front();candidate.path.assign(raw.begin()+1,raw.end());candidate.reads=std::move(read);
    }
    output.candidates.push_back(std::move(candidate));
   }
  }
  std::sort(output.candidates.begin(),output.candidates.end(),[](const auto& a,const auto& b){return std::tie(a.task.priority,a.task.id)<std::tie(b.task.priority,b.task.id);});
  std::vector<Task> commit_tasks;std::vector<std::uint32_t> paths;std::vector<ReadEntry> reads;std::vector<PathResult> results;
  for(const auto& candidate:output.candidates){
   if(candidate.path.size()>65535U||candidate.reads.size()>65535U)throw std::runtime_error("XRT transaction exceeds record ABI");
   PathResult result{};result.offset=paths.size();result.length=candidate.path.size();result.status=candidate.search_status;
   result.read_offset=reads.size();result.read_count=candidate.reads.size();commit_tasks.push_back(candidate.task);
   paths.insert(paths.end(),candidate.path.begin(),candidate.path.end());reads.insert(reads.end(),candidate.reads.begin(),candidate.reads.end());results.push_back(result);
  }
  if(paths.size()>4*tx_capacity_||reads.size()>4*tx_capacity_)throw std::runtime_error("XRT commit pool overflow");
  upload(*commit_tasks_,commit_tasks);upload(*commit_paths_,paths);upload(*commit_reads_,reads);upload(*commit_results_,results);
  output.telemetry.h2d_bytes+=commit_tasks.size()*sizeof(Task)+paths.size()*sizeof(std::uint32_t)+reads.size()*sizeof(ReadEntry)+results.size()*sizeof(PathResult);
  const auto capacity=std::max<std::size_t>({paths.size(),reads.size(),1});const auto commit_begin=std::chrono::steady_clock::now();
  auto run=commit_(*pes_[0].resources,*pes_[1].resources,*pes_[2].resources,*pes_[3].resources,
   *commit_tasks_,*commit_paths_,*commit_reads_,*commit_results_,resources.size(),results.size(),capacity,
   allow_overuse?1U:0U,*commit_metrics_);++output.telemetry.commit_launches;run.wait();
  output.telemetry.commit_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-commit_begin).count();
  download(*commit_results_,results);std::vector<Metrics> metric(1);download(*commit_metrics_,metric);
  output.telemetry.d2h_bytes+=results.size()*sizeof(PathResult)+sizeof(Metrics);output.commit_metrics=metric[0];
  for(std::size_t i=0;i<results.size();++i)output.candidates[i].commit_status=results[i].status;
  mirror_commits(resources,output.candidates);return output;
 }

private:
 void sync_resources(const std::vector<Resource>& resources,KernelBatchTelemetry& telemetry){
  if(device_shadow_.size()!=resources.size()){
   device_shadow_=resources;for(auto& pe:pes_)upload(*pe.resources,resources);
   telemetry.h2d_bytes+=4ULL*resources.size()*sizeof(Resource);return;
  }
  std::size_t begin=0;
  while(begin<resources.size()){
   while(begin<resources.size()&&std::memcmp(&resources[begin],&device_shadow_[begin],sizeof(Resource))==0)++begin;
   if(begin==resources.size())break;
   std::size_t end=begin+1;
   while(end<resources.size()&&std::memcmp(&resources[end],&device_shadow_[end],sizeof(Resource))!=0)++end;
   const std::size_t bytes=(end-begin)*sizeof(Resource),offset=begin*sizeof(Resource);
   for(auto& pe:pes_){std::memcpy(static_cast<unsigned char*>(pe.resources->map<void*>())+offset,resources.data()+begin,bytes);pe.resources->sync(XCL_BO_SYNC_BO_TO_DEVICE,bytes,offset);}
   telemetry.h2d_bytes+=4ULL*bytes;std::copy(resources.begin()+begin,resources.begin()+end,device_shadow_.begin()+begin);begin=end;
  }
 }

 void mirror_commits(std::vector<Resource>& resources,const std::vector<KernelCandidate>& candidates){
  for(const auto& candidate:candidates){
   if(candidate.commit_status!=4)continue;
   for(const auto id:candidate.path){
    if(id>=resources.size())throw std::runtime_error("committed XRT path exceeds resources");
    Resource state=resources[id];if(state.owner==candidate.task.net_id)continue;
    const std::uint16_t prior=state.occupancy;if(state.occupancy!=65535U)++state.occupancy;
    ++state.version;state.owner=prior==0?candidate.task.net_id:INVALID_RESOURCE;
    resources[id]=state;device_shadow_[id]=state;
   }
  }
 }

 std::vector<Node> nodes_;std::vector<Edge> edges_;std::vector<Resource> device_shadow_;
 std::uint32_t pe_count_,queue_depth_,tasks_per_cu_;std::size_t active_queue_,tx_capacity_,batch_capacity_;
 std::uint64_t setup_h2d_bytes_=0;xrt::device device_;xrt::uuid uuid_;xrt::kernel commit_;
 std::vector<SearchPe> pes_;std::unique_ptr<xrt::bo> commit_tasks_,commit_paths_,commit_reads_,commit_results_,commit_metrics_;
};

int main(int argc,char** argv){try{
 if(argc!=4&&argc!=5){std::cerr<<"usage: persistroute_accelerated_xrt <xclbin> <input-prefix> <output-prefix> [golden-prefix]\n";return 2;}const auto begin=std::chrono::steady_clock::now();const std::string xclbin=argv[1],input=argv[2],output=argv[3];
 const auto nodes=read_array<Node>(input+".nodes");const auto edges=read_array<Edge>(input+".edges");const auto initial=read_array<Resource>(input+".resources");const auto tasks=read_array<Task>(input+".tasks");PathfinderConfig config;config.max_iterations=env_u32("PERSISTROUTE_MAX_ITERATIONS",config.max_iterations);config.min_timing_iterations=env_u32("PERSISTROUTE_MIN_TIMING_ITERATIONS",config.min_timing_iterations);config.timing_update_period=env_u32("PERSISTROUTE_TIMING_UPDATE_PERIOD",config.timing_update_period);config.adaptive_issue_width_min=env_u32("PERSISTROUTE_ADAPTIVE_ISSUE_MIN",config.adaptive_issue_width_min);config.adaptive_issue_stagnation_iterations=env_u32("PERSISTROUTE_ADAPTIVE_ISSUE_STAGNATION",config.adaptive_issue_stagnation_iterations);config.present_start_q=env_u16("PERSISTROUTE_PRESENT_START_Q",config.present_start_q);config.present_multiplier_q=env_u16("PERSISTROUTE_PRESENT_MULTIPLIER_Q",config.present_multiplier_q);config.history_increment_q=env_u16("PERSISTROUTE_HISTORY_INCREMENT_Q",config.history_increment_q);const auto pes=env_u32("PERSISTROUTE_PE_COUNT",4),tasks_per_cu=env_u32("PERSISTROUTE_TASKS_PER_CU",1),issue=env_u32("PERSISTROUTE_ISSUE_WIDTH",pes*tasks_per_cu),queue_depth=env_u32("PERSISTROUTE_QUEUE_DEPTH",0),tx_capacity=env_u32("PERSISTROUTE_TX_CAPACITY",0);
 XrtExecutor xrt(xclbin,nodes,edges,pes,queue_depth,tasks_per_cu,tx_capacity);KernelBatchExecutor executor=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool over){return xrt(n,e,r,t,s,over);};TimingAnalyzer timing_analyzer;const char* timing_command=std::getenv("PERSISTROUTE_TIMING_COMMAND");if(timing_command&&*timing_command)timing_analyzer=make_external_timing_analyzer(timing_command,output);const auto accelerated=route_accelerated_pathfinder(nodes,edges,initial,tasks,executor,config,issue,timing_analyzer);const auto routed=std::chrono::steady_clock::now();const auto& result=accelerated.routing;
 std::ofstream paths(output+".paths.csv");paths<<"task_id,path_index,resource_id\n";for(const auto& task:result.tasks)for(std::size_t i=0;i<task.path.size();++i)paths<<task.task.id<<','<<i<<','<<task.path[i]<<'\n';std::ofstream trees(output+".route_trees.csv");trees<<"net_id,source,parent,child\n";for(const auto& tree:result.route_trees)for(const auto& edge:tree.edges)trees<<tree.net_id<<','<<tree.source<<','<<edge.parent<<','<<edge.child<<'\n';std::ofstream iterations(output+".iterations.csv");iterations<<"iteration,routed_nets,failed_connections,overused_resources,present_factor_q\n";for(const auto& item:result.iteration_log)iterations<<item.iteration<<','<<item.routed_nets<<','<<item.failed_connections<<','<<item.overused_resources<<','<<item.present_factor_q<<'\n';std::ofstream timing(output+".timing_iterations.csv");timing<<"iteration,updated_connections,min_criticality_q,max_criticality_q,critical_path_delay_ps\n";for(const auto& item:result.timing_log)timing<<item.iteration<<','<<item.updated_connections<<','<<item.min_criticality_q<<','<<item.max_criticality_q<<','<<item.critical_path_delay_ps<<'\n';std::ofstream audit(output+".accelerated_iterations.csv");audit<<"iteration,issue_width,waves,launched,committed,failed,overused_resources,resource_hash,route_hash\n";for(const auto& item:accelerated.audit)audit<<std::dec<<item.iteration<<','<<item.issue_width<<','<<item.waves<<','<<item.launched<<','<<item.committed<<','<<item.failed<<','<<item.overused_resources<<','<<std::hex<<std::setw(16)<<std::setfill('0')<<item.resource_hash<<','<<std::setw(16)<<item.route_hash<<'\n';std::ofstream performance(output+".performance_iterations.csv");performance<<"iteration,h2d_bytes,d2h_bytes,search_ns,commit_ns,search_launches,commit_launches\n";for(const auto& item:accelerated.audit)performance<<std::dec<<item.iteration<<','<<item.telemetry.h2d_bytes<<','<<item.telemetry.d2h_bytes<<','<<item.telemetry.search_ns<<','<<item.telemetry.commit_ns<<','<<item.telemetry.search_launches<<','<<item.telemetry.commit_launches<<'\n';write_array(output+".resources",result.resources);paths.close();trees.close();iterations.close();timing.close();audit.close();performance.close();
 bool golden=true;if(argc==5){const std::string expected=argv[4];for(const std::string suffix:{".paths.csv",".route_trees.csv",".iterations.csv",".accelerated_iterations.csv",".resources"})golden=golden&&slurp(output+suffix)==slurp(expected+suffix);if(timing_analyzer)golden=golden&&slurp(output+".timing_iterations.csv")==slurp(expected+".timing_iterations.csv");}
 const auto end=std::chrono::steady_clock::now();const auto ms=[](auto a,auto b){return std::chrono::duration<double,std::milli>(b-a).count();};std::cout<<"{\"backend\":\"xrt\",\"legal\":"<<(result.legal?"true":"false")<<",\"golden_match\":"<<(golden?"true":"false")<<",\"tasks\":"<<tasks.size()<<",\"iterations\":"<<result.metrics.iterations<<",\"searches\":"<<result.metrics.searches<<",\"overused_resources\":"<<result.metrics.overused_resources<<",\"h2d_bytes\":"<<accelerated.telemetry.h2d_bytes<<",\"d2h_bytes\":"<<accelerated.telemetry.d2h_bytes<<",\"search_launches\":"<<accelerated.telemetry.search_launches<<",\"commit_launches\":"<<accelerated.telemetry.commit_launches<<",\"search_ms\":"<<accelerated.telemetry.search_ns/1.0e6<<",\"commit_ms\":"<<accelerated.telemetry.commit_ns/1.0e6<<",\"timing_ms\":"<<accelerated.timing_ns/1.0e6<<",\"route_ms\":"<<ms(begin,routed)<<",\"wall_ms\":"<<ms(begin,end)<<"}\n";return result.legal&&golden?0:3;
 }catch(const std::exception& error){std::cerr<<"error: "<<error.what()<<'\n';return 1;}}
