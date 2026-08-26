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

struct SearchPe {std::unique_ptr<xrt::kernel> kernel;std::unique_ptr<xrt::bo> nodes,edges,resources,task,path,reads,result,distance,predecessor,hops,seen,closed,read_epoch,queue,sizes,metrics;};

class XrtExecutor {
public:
 XrtExecutor(const std::string& xclbin,const std::vector<Node>& nodes,const std::vector<Edge>& edges,std::uint32_t pe_count,std::uint32_t queue_depth)
     : nodes_(nodes),edges_(edges),pe_count_(pe_count),queue_depth_(queue_depth?queue_depth:std::max<std::uint32_t>(256,(8ULL*nodes.size()+MQ_QUEUES-1)/MQ_QUEUES)),
       active_queue_(static_cast<std::size_t>(MQ_QUEUES)*queue_depth_),tx_capacity_(nodes.size()+1),device_(0),uuid_(device_.load_xclbin(xclbin)),commit_(device_,uuid_,"commit_hbm_kernel:{commit_hbm_kernel_1}") {
  if(pe_count_==0||pe_count_>4||nodes_.empty())throw std::invalid_argument("XRT PE count/graph is invalid");
  auto commit_bo=[&](std::size_t bytes,int arg){return std::make_unique<xrt::bo>(device_,std::max<std::size_t>(bytes,64),commit_.group_id(arg));};
  commit_resources_=commit_bo(nodes.size()*sizeof(Resource),0);commit_tasks_=commit_bo(pe_count_*sizeof(Task),1);commit_paths_=commit_bo(pe_count_*tx_capacity_*sizeof(std::uint32_t),2);commit_reads_=commit_bo(pe_count_*tx_capacity_*sizeof(ReadEntry),3);commit_results_=commit_bo(pe_count_*sizeof(PathResult),4);commit_metrics_=commit_bo(sizeof(Metrics),9);
  pes_.resize(pe_count_);
  for(std::uint32_t i=0;i<pe_count_;++i){auto& pe=pes_[i];pe.kernel=std::make_unique<xrt::kernel>(device_,uuid_,"search_hbm_kernel:{search_hbm_kernel_"+std::to_string(i+1)+"}");auto make=[&](std::size_t bytes,int arg){return std::make_unique<xrt::bo>(device_,std::max<std::size_t>(bytes,64),pe.kernel->group_id(arg));};
   pe.nodes=make(nodes.size()*sizeof(Node),0);pe.edges=make(edges.size()*sizeof(Edge),1);pe.resources=make(nodes.size()*sizeof(Resource),2);pe.task=make(sizeof(Task),3);pe.path=make(tx_capacity_*sizeof(std::uint32_t),4);pe.reads=make(tx_capacity_*sizeof(ReadEntry),5);pe.result=make(sizeof(PathResult),6);pe.distance=make(nodes.size()*sizeof(std::uint32_t),7);pe.predecessor=make(nodes.size()*sizeof(std::uint32_t),8);pe.hops=make(nodes.size()*sizeof(std::uint32_t),9);pe.seen=make(nodes.size()*sizeof(std::uint32_t),10);pe.closed=make(nodes.size()*sizeof(std::uint32_t),11);pe.read_epoch=make(nodes.size()*sizeof(std::uint32_t),12);pe.queue=make((active_queue_+nodes.size())*sizeof(MQEntry),13);pe.sizes=make(MQ_QUEUES*sizeof(std::uint32_t),14);pe.metrics=make(sizeof(Metrics),20);upload(*pe.nodes,nodes_);upload(*pe.edges,edges_);
  }
 }

 KernelBatchResult operator()(const std::vector<Node>&,const std::vector<Edge>&,std::vector<Resource>& resources,const std::vector<Task>& tasks,const std::vector<std::vector<SearchSeed>>& seeds,bool allow_overuse){
  if(tasks.size()!=seeds.size()||tasks.size()>pe_count_)
   throw std::invalid_argument("XRT batch exceeds configured CUs");
  KernelBatchResult output;if(tasks.empty())return output;upload(*commit_resources_,resources);
  std::vector<xrt::run> runs;std::vector<Task> kernel_tasks(tasks);runs.reserve(tasks.size());
  for(std::size_t i=0;i<tasks.size();++i){auto& pe=pes_[i];if(seeds[i].empty()||seeds[i].size()>nodes_.size())throw std::runtime_error("invalid XRT seed list");kernel_tasks[i].epoch=seeds[i].size();kernel_tasks[i].reserved=active_queue_;
   std::vector<Task> one{kernel_tasks[i]};std::vector<MQEntry> seed_entries;for(const auto& seed:seeds[i])seed_entries.push_back({seed.node,INVALID_RESOURCE,0,seed.hops});upload(*pe.resources,resources);upload(*pe.task,one);upload(*pe.queue,seed_entries,active_queue_*sizeof(MQEntry));
   runs.push_back((*pe.kernel)(*pe.nodes,*pe.edges,*pe.resources,*pe.task,*pe.path,*pe.reads,*pe.result,*pe.distance,*pe.predecessor,*pe.hops,*pe.seen,*pe.closed,*pe.read_epoch,*pe.queue,*pe.sizes,nodes_.size(),edges_.size(),1U,queue_depth_,tx_capacity_,*pe.metrics));
  }
  for(auto& run:runs)run.wait();
  for(std::size_t i=0;i<tasks.size();++i){auto& pe=pes_[i];std::vector<PathResult> result(1);std::vector<Metrics> metric(1);download(*pe.result,result);download(*pe.metrics,metric);output.search_metrics.expanded+=metric[0].expanded;output.search_metrics.edge_visits+=metric[0].edge_visits;output.search_metrics.failed+=metric[0].failed;KernelCandidate candidate{};candidate.task=tasks[i];candidate.search_status=result[0].status;candidate.commit_status=result[0].status;
   if(result[0].status==1){std::vector<std::uint32_t> raw(result[0].length);std::vector<ReadEntry> read(result[0].read_count);download(*pe.path,raw,result[0].offset*sizeof(std::uint32_t));download(*pe.reads,read,result[0].read_offset*sizeof(ReadEntry));if(raw.empty())throw std::runtime_error("XRT multi-source result omitted attachment");candidate.attachment=raw.front();candidate.path.assign(raw.begin()+1,raw.end());candidate.reads=std::move(read);}output.candidates.push_back(std::move(candidate));
  }
  std::vector<Task> commit_tasks;std::vector<std::uint32_t> paths;std::vector<ReadEntry> reads;std::vector<PathResult> results;
  for(const auto& c:output.candidates){PathResult r{};r.offset=paths.size();r.length=c.path.size();r.status=c.search_status;r.read_offset=reads.size();r.read_count=c.reads.size();commit_tasks.push_back(c.task);paths.insert(paths.end(),c.path.begin(),c.path.end());reads.insert(reads.end(),c.reads.begin(),c.reads.end());results.push_back(r);}
  upload(*commit_tasks_,commit_tasks);upload(*commit_paths_,paths);upload(*commit_reads_,reads);upload(*commit_results_,results);const auto capacity=std::max<std::size_t>({paths.size(),reads.size(),1});auto run=commit_(*commit_resources_,*commit_tasks_,*commit_paths_,*commit_reads_,*commit_results_,resources.size(),tasks.size(),capacity,allow_overuse?1U:0U,*commit_metrics_);run.wait();download(*commit_results_,results);download(*commit_resources_,resources);std::vector<Metrics> metric(1);download(*commit_metrics_,metric);output.commit_metrics=metric[0];for(std::size_t i=0;i<results.size();++i)output.candidates[i].commit_status=results[i].status;return output;
 }

private:
 std::vector<Node> nodes_;std::vector<Edge> edges_;std::uint32_t pe_count_,queue_depth_;std::size_t active_queue_,tx_capacity_;xrt::device device_;xrt::uuid uuid_;xrt::kernel commit_;std::vector<SearchPe> pes_;std::unique_ptr<xrt::bo> commit_resources_,commit_tasks_,commit_paths_,commit_reads_,commit_results_,commit_metrics_;
};

int main(int argc,char** argv){try{
 if(argc!=4&&argc!=5){std::cerr<<"usage: persistroute_accelerated_xrt <xclbin> <input-prefix> <output-prefix> [golden-prefix]\n";return 2;}const auto begin=std::chrono::steady_clock::now();const std::string xclbin=argv[1],input=argv[2],output=argv[3];
 const auto nodes=read_array<Node>(input+".nodes");const auto edges=read_array<Edge>(input+".edges");const auto initial=read_array<Resource>(input+".resources");const auto tasks=read_array<Task>(input+".tasks");PathfinderConfig config;config.max_iterations=env_u32("PERSISTROUTE_MAX_ITERATIONS",config.max_iterations);config.min_timing_iterations=env_u32("PERSISTROUTE_MIN_TIMING_ITERATIONS",config.min_timing_iterations);config.present_start_q=env_u16("PERSISTROUTE_PRESENT_START_Q",config.present_start_q);config.present_multiplier_q=env_u16("PERSISTROUTE_PRESENT_MULTIPLIER_Q",config.present_multiplier_q);config.history_increment_q=env_u16("PERSISTROUTE_HISTORY_INCREMENT_Q",config.history_increment_q);const auto pes=env_u32("PERSISTROUTE_PE_COUNT",4),issue=env_u32("PERSISTROUTE_ISSUE_WIDTH",pes),queue_depth=env_u32("PERSISTROUTE_QUEUE_DEPTH",0);
 XrtExecutor xrt(xclbin,nodes,edges,pes,queue_depth);KernelBatchExecutor executor=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool over){return xrt(n,e,r,t,s,over);};TimingAnalyzer timing_analyzer;const char* timing_command=std::getenv("PERSISTROUTE_TIMING_COMMAND");if(timing_command&&*timing_command)timing_analyzer=make_external_timing_analyzer(timing_command,output);const auto accelerated=route_accelerated_pathfinder(nodes,edges,initial,tasks,executor,config,issue,timing_analyzer);const auto routed=std::chrono::steady_clock::now();const auto& result=accelerated.routing;
 std::ofstream paths(output+".paths.csv");paths<<"task_id,path_index,resource_id\n";for(const auto& task:result.tasks)for(std::size_t i=0;i<task.path.size();++i)paths<<task.task.id<<','<<i<<','<<task.path[i]<<'\n';std::ofstream trees(output+".route_trees.csv");trees<<"net_id,source,parent,child\n";for(const auto& tree:result.route_trees)for(const auto& edge:tree.edges)trees<<tree.net_id<<','<<tree.source<<','<<edge.parent<<','<<edge.child<<'\n';std::ofstream iterations(output+".iterations.csv");iterations<<"iteration,routed_nets,failed_connections,overused_resources,present_factor_q\n";for(const auto& item:result.iteration_log)iterations<<item.iteration<<','<<item.routed_nets<<','<<item.failed_connections<<','<<item.overused_resources<<','<<item.present_factor_q<<'\n';std::ofstream timing(output+".timing_iterations.csv");timing<<"iteration,updated_connections,min_criticality_q,max_criticality_q,critical_path_delay_ps\n";for(const auto& item:result.timing_log)timing<<item.iteration<<','<<item.updated_connections<<','<<item.min_criticality_q<<','<<item.max_criticality_q<<','<<item.critical_path_delay_ps<<'\n';std::ofstream audit(output+".accelerated_iterations.csv");audit<<"iteration,waves,launched,committed,failed,overused_resources,resource_hash,route_hash\n";for(const auto& item:accelerated.audit)audit<<std::dec<<item.iteration<<','<<item.waves<<','<<item.launched<<','<<item.committed<<','<<item.failed<<','<<item.overused_resources<<','<<std::hex<<std::setw(16)<<std::setfill('0')<<item.resource_hash<<','<<std::setw(16)<<item.route_hash<<'\n';write_array(output+".resources",result.resources);paths.close();trees.close();iterations.close();timing.close();audit.close();
 bool golden=true;if(argc==5){const std::string expected=argv[4];for(const std::string suffix:{".paths.csv",".route_trees.csv",".iterations.csv",".accelerated_iterations.csv",".resources"})golden=golden&&slurp(output+suffix)==slurp(expected+suffix);if(timing_analyzer)golden=golden&&slurp(output+".timing_iterations.csv")==slurp(expected+".timing_iterations.csv");}
 const auto end=std::chrono::steady_clock::now();const auto ms=[](auto a,auto b){return std::chrono::duration<double,std::milli>(b-a).count();};std::cout<<"{\"backend\":\"xrt\",\"legal\":"<<(result.legal?"true":"false")<<",\"golden_match\":"<<(golden?"true":"false")<<",\"tasks\":"<<tasks.size()<<",\"iterations\":"<<result.metrics.iterations<<",\"searches\":"<<result.metrics.searches<<",\"overused_resources\":"<<result.metrics.overused_resources<<",\"route_ms\":"<<ms(begin,routed)<<",\"wall_ms\":"<<ms(begin,end)<<"}\n";return result.legal&&golden?0:3;
 }catch(const std::exception& error){std::cerr<<"error: "<<error.what()<<'\n';return 1;}}
