#include "accelerated_pathfinder.hpp"
#include "external_timing.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

using namespace persistroute;
static_assert(sizeof(Node)==8&&sizeof(Edge)==8&&sizeof(Resource)==16&&sizeof(Task)==32,
              "host/kernel ABI mismatch");

template<typename T>std::vector<T> read_array(const std::string& path){
 static_assert(std::is_trivially_copyable<T>::value,"binary records must be trivially copyable");
 std::ifstream input(path,std::ios::binary|std::ios::ate);if(!input)throw std::runtime_error("cannot open "+path);
 const auto end=input.tellg();if(end<0||static_cast<std::uint64_t>(end)%sizeof(T))throw std::runtime_error("misaligned "+path);
 std::vector<T> values(static_cast<std::size_t>(end)/sizeof(T));input.seekg(0);if(!values.empty())input.read(reinterpret_cast<char*>(values.data()),values.size()*sizeof(T));if(!input)throw std::runtime_error("cannot read "+path);return values;
}
template<typename T>void write_array(const std::string& path,const std::vector<T>& values){std::ofstream out(path,std::ios::binary);if(!out)throw std::runtime_error("cannot create "+path);if(!values.empty())out.write(reinterpret_cast<const char*>(values.data()),values.size()*sizeof(T));if(!out)throw std::runtime_error("cannot write "+path);}
std::uint32_t env_u32(const char* name,std::uint32_t fallback){const char* text=std::getenv(name);if(!text)return fallback;std::size_t used=0;const unsigned long value=std::stoul(text,&used,0);if(text[used]||value>0xffffffffUL)throw std::runtime_error(std::string("bad ")+name);return value;}
std::uint16_t env_u16(const char* name,std::uint16_t fallback){const auto value=env_u32(name,fallback);if(value>65535U)throw std::runtime_error(std::string("bad ")+name);return value;}

int main(int argc,char** argv){try{
 if(argc!=3){std::cerr<<"usage: persistroute_accelerated_cmodel <input-prefix> <output-prefix>\n";return 2;}
 const auto begin=std::chrono::steady_clock::now();const std::string input=argv[1],output=argv[2];
 const auto nodes=read_array<Node>(input+".nodes");const auto edges=read_array<Edge>(input+".edges");
 const auto initial=read_array<Resource>(input+".resources");const auto tasks=read_array<Task>(input+".tasks");
 PathfinderConfig config;config.max_iterations=env_u32("PERSISTROUTE_MAX_ITERATIONS",config.max_iterations);config.min_timing_iterations=env_u32("PERSISTROUTE_MIN_TIMING_ITERATIONS",config.min_timing_iterations);config.timing_update_period=env_u32("PERSISTROUTE_TIMING_UPDATE_PERIOD",config.timing_update_period);config.present_start_q=env_u16("PERSISTROUTE_PRESENT_START_Q",config.present_start_q);config.present_multiplier_q=env_u16("PERSISTROUTE_PRESENT_MULTIPLIER_Q",config.present_multiplier_q);config.history_increment_q=env_u16("PERSISTROUTE_HISTORY_INCREMENT_Q",config.history_increment_q);
 SelectiveCleanupConfig cleanup;cleanup.passes=env_u32("PERSISTROUTE_SELECTIVE_CLEANUP_PASSES",0);cleanup.channel_length_cost_q=env_u16("PERSISTROUTE_CLEANUP_LENGTH_COST_Q",0);cleanup.delay_tolerance_ppm=env_u32("PERSISTROUTE_CLEANUP_DELAY_TOLERANCE_PPM",0);cleanup.branch_budget_ppm=env_u32("PERSISTROUTE_CLEANUP_BRANCH_BUDGET_PPM",0);cleanup.max_branches=env_u32("PERSISTROUTE_CLEANUP_MAX_BRANCHES",0);cleanup.time_budget_ms=env_u32("PERSISTROUTE_CLEANUP_TIME_BUDGET_MS",0);cleanup.per_connection_delay_guard=env_u32("PERSISTROUTE_CLEANUP_PER_CONNECTION_DELAY_GUARD",1)!=0;
 const std::uint32_t pes=env_u32("PERSISTROUTE_PE_COUNT",4),issue_width=env_u32("PERSISTROUTE_ISSUE_WIDTH",pes),queue_depth=env_u32("PERSISTROUTE_QUEUE_DEPTH",0),tx_capacity=env_u32("PERSISTROUTE_TX_CAPACITY",0);
 KernelBatchExecutor executor=[=](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool over){return execute_hbm_cmodel_batch(n,e,r,t,s,over,pes,queue_depth,tx_capacity);};
 TimingAnalyzer timing_analyzer;const char* timing_command=std::getenv("PERSISTROUTE_TIMING_COMMAND");if(timing_command&&*timing_command)timing_analyzer=make_external_timing_analyzer(timing_command,output);
 const auto accelerated=route_accelerated_pathfinder(nodes,edges,initial,tasks,executor,config,issue_width,timing_analyzer,cleanup);const auto routed=std::chrono::steady_clock::now();const auto& result=accelerated.routing;
 std::ofstream paths(output+".paths.csv");paths<<"task_id,path_index,resource_id\n";for(const auto& task:result.tasks)for(std::size_t i=0;i<task.path.size();++i)paths<<task.task.id<<','<<i<<','<<task.path[i]<<'\n';
 std::ofstream trees(output+".route_trees.csv");trees<<"net_id,source,parent,child\n";for(const auto& tree:result.route_trees)for(const auto& edge:tree.edges)trees<<tree.net_id<<','<<tree.source<<','<<edge.parent<<','<<edge.child<<'\n';
 std::ofstream iterations(output+".iterations.csv");iterations<<"iteration,routed_nets,failed_connections,overused_resources,present_factor_q\n";for(const auto& item:result.iteration_log)iterations<<item.iteration<<','<<item.routed_nets<<','<<item.failed_connections<<','<<item.overused_resources<<','<<item.present_factor_q<<'\n';
 std::ofstream timing(output+".timing_iterations.csv");timing<<"iteration,updated_connections,min_criticality_q,max_criticality_q,critical_path_delay_ps\n";for(const auto& item:result.timing_log)timing<<item.iteration<<','<<item.updated_connections<<','<<item.min_criticality_q<<','<<item.max_criticality_q<<','<<item.critical_path_delay_ps<<'\n';
 std::ofstream audit(output+".accelerated_iterations.csv");audit<<"iteration,waves,launched,committed,failed,overused_resources,resource_hash,route_hash\n";for(const auto& item:accelerated.audit)audit<<std::dec<<item.iteration<<','<<item.waves<<','<<item.launched<<','<<item.committed<<','<<item.failed<<','<<item.overused_resources<<','<<std::hex<<std::setw(16)<<std::setfill('0')<<item.resource_hash<<','<<std::setw(16)<<item.route_hash<<'\n';
 std::ofstream performance(output+".performance_iterations.csv");performance<<"iteration,h2d_bytes,d2h_bytes,search_ns,commit_ns,search_launches,commit_launches\n";for(const auto& item:accelerated.audit)performance<<std::dec<<item.iteration<<','<<item.telemetry.h2d_bytes<<','<<item.telemetry.d2h_bytes<<','<<item.telemetry.search_ns<<','<<item.telemetry.commit_ns<<','<<item.telemetry.search_launches<<','<<item.telemetry.commit_launches<<'\n';
 write_array(output+".resources",result.resources);paths.close();trees.close();iterations.close();timing.close();audit.close();performance.close();if(!paths||!trees||!iterations||!timing||!audit||!performance)throw std::runtime_error("failed writing accelerated outputs");
 const auto end=std::chrono::steady_clock::now();const auto ms=[](auto a,auto b){return std::chrono::duration<double,std::milli>(b-a).count();};const auto count=std::count_if(result.tasks.begin(),result.tasks.end(),[](const auto& task){return task.routed;});
 std::cout<<"{\"backend\":\"hbm_cmodel\",\"legal\":"<<(result.legal?"true":"false")<<",\"tasks\":"<<tasks.size()<<",\"routed_tasks\":"<<count<<",\"iterations\":"<<result.metrics.iterations<<",\"searches\":"<<result.metrics.searches<<",\"expanded\":"<<result.metrics.expanded<<",\"edge_visits\":"<<result.metrics.edge_visits<<",\"overused_resources\":"<<result.metrics.overused_resources<<",\"cleanup_attempted_nets\":"<<accelerated.cleanup_attempted_nets<<",\"cleanup_accepted_nets\":"<<accelerated.cleanup_accepted_nets<<",\"cleanup_attempted_branches\":"<<accelerated.cleanup_attempted_branches<<",\"cleanup_accepted_branches\":"<<accelerated.cleanup_accepted_branches<<",\"cleanup_wirelength_before\":"<<accelerated.cleanup_wirelength_before<<",\"cleanup_wirelength_after\":"<<accelerated.cleanup_wirelength_after<<",\"h2d_bytes\":"<<accelerated.telemetry.h2d_bytes<<",\"d2h_bytes\":"<<accelerated.telemetry.d2h_bytes<<",\"search_launches\":"<<accelerated.telemetry.search_launches<<",\"commit_launches\":"<<accelerated.telemetry.commit_launches<<",\"search_ms\":"<<accelerated.telemetry.search_ns/1.0e6<<",\"commit_ms\":"<<accelerated.telemetry.commit_ns/1.0e6<<",\"timing_ms\":"<<accelerated.timing_ns/1.0e6<<",\"cleanup_ms\":"<<accelerated.cleanup_ns/1.0e6<<",\"route_ms\":"<<ms(begin,routed)<<",\"wall_ms\":"<<ms(begin,end)<<"}\n";
 return result.legal?0:3;
 }catch(const std::exception& error){std::cerr<<"error: "<<error.what()<<'\n';return 1;}}
