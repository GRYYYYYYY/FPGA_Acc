#include "pathfinder.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

using namespace persistroute;

static_assert(sizeof(Node)==8&&sizeof(Edge)==8&&sizeof(Resource)==16&&sizeof(Task)==32,
              "host/kernel ABI mismatch");

template<typename T>
std::vector<T> read_array(const std::string& path) {
 static_assert(std::is_trivially_copyable<T>::value,"binary ABI records must be trivially copyable");
 std::ifstream input(path,std::ios::binary|std::ios::ate);
 if(!input)throw std::runtime_error("cannot open "+path);
 const auto end=input.tellg();
 if(end<0||static_cast<std::uint64_t>(end)%sizeof(T)!=0)throw std::runtime_error("misaligned "+path);
 std::vector<T> values(static_cast<std::size_t>(end)/sizeof(T));
 input.seekg(0);
 if(!values.empty())input.read(reinterpret_cast<char*>(values.data()),static_cast<std::streamsize>(values.size()*sizeof(T)));
 if(!input)throw std::runtime_error("cannot read "+path);
 return values;
}

template<typename T>
void write_array(const std::string& path,const std::vector<T>& values) {
 std::ofstream output(path,std::ios::binary);
 if(!output)throw std::runtime_error("cannot create "+path);
 if(!values.empty())output.write(reinterpret_cast<const char*>(values.data()),static_cast<std::streamsize>(values.size()*sizeof(T)));
 if(!output)throw std::runtime_error("cannot write "+path);
}

std::uint32_t env_u32(const char* name,std::uint32_t fallback) {
 const char* text=std::getenv(name);
 if(text==nullptr)return fallback;
 std::size_t consumed=0;const unsigned long value=std::stoul(text,&consumed,0);
 if(text[consumed]!='\0'||value>0xffffffffUL)throw std::runtime_error(std::string("bad ")+name);
 return static_cast<std::uint32_t>(value);
}

std::uint16_t env_u16(const char* name,std::uint16_t fallback) {
 const std::uint32_t value=env_u32(name,fallback);
 if(value>65535U)throw std::runtime_error(std::string("bad ")+name);
 return static_cast<std::uint16_t>(value);
}

int main(int argc,char** argv) {
 try {
  if(argc!=3){std::cerr<<"usage: persistroute_pathfinder <input-prefix> <output-prefix>\n";return 2;}
  const auto begin=std::chrono::steady_clock::now();const std::string input=argv[1],output=argv[2];
  const auto nodes=read_array<Node>(input+".nodes");const auto edges=read_array<Edge>(input+".edges");
  const auto resources=read_array<Resource>(input+".resources");const auto tasks=read_array<Task>(input+".tasks");
  PathfinderConfig config;
  config.max_iterations=env_u32("PERSISTROUTE_MAX_ITERATIONS",config.max_iterations);
  config.present_start_q=env_u16("PERSISTROUTE_PRESENT_START_Q",config.present_start_q);
  config.present_multiplier_q=env_u16("PERSISTROUTE_PRESENT_MULTIPLIER_Q",config.present_multiplier_q);
  config.history_increment_q=env_u16("PERSISTROUTE_HISTORY_INCREMENT_Q",config.history_increment_q);
  const PathfinderResult result=route_pathfinder(nodes,edges,resources,tasks,config);
  const auto routed=std::chrono::steady_clock::now();

  std::ofstream paths(output+".paths.csv");
  if(!paths)throw std::runtime_error("cannot create "+output+".paths.csv");
  paths<<"task_id,path_index,resource_id\n";
  for(const auto& task:result.tasks)for(std::size_t i=0;i<task.path.size();++i)
   paths<<task.task.id<<','<<i<<','<<task.path[i]<<'\n';

  std::ofstream trees(output+".route_trees.csv");
  if(!trees)throw std::runtime_error("cannot create "+output+".route_trees.csv");
  trees<<"net_id,source,parent,child\n";
  for(const auto& tree:result.route_trees)for(const auto& edge:tree.edges)
   trees<<tree.net_id<<','<<tree.source<<','<<edge.parent<<','<<edge.child<<'\n';

  std::ofstream iterations(output+".iterations.csv");
  if(!iterations)throw std::runtime_error("cannot create "+output+".iterations.csv");
  iterations<<"iteration,routed_nets,failed_connections,overused_resources,present_factor_q\n";
  for(const auto& item:result.iteration_log)
   iterations<<item.iteration<<','<<item.routed_nets<<','<<item.failed_connections<<','
             <<item.overused_resources<<','<<item.present_factor_q<<'\n';
  write_array(output+".resources",result.resources);
  paths.close();trees.close();iterations.close();
  if(!paths||!trees||!iterations)throw std::runtime_error("failed while writing route outputs");

  const auto end=std::chrono::steady_clock::now();
  const auto millis=[](auto first,auto last){return std::chrono::duration<double,std::milli>(last-first).count();};
  const std::size_t routed_tasks=static_cast<std::size_t>(std::count_if(
      result.tasks.begin(),result.tasks.end(),[](const RoutedTask& task){return task.routed;}));
  const std::string json="{\"legal\":"+std::string(result.legal?"true":"false")+
   ",\"route_success\":"+std::string(result.route_success?"true":"false")+
   ",\"tasks\":"+std::to_string(result.tasks.size())+
   ",\"routed_tasks\":"+std::to_string(routed_tasks)+
   ",\"iterations\":"+std::to_string(result.metrics.iterations)+
   ",\"searches\":"+std::to_string(result.metrics.searches)+
   ",\"expanded\":"+std::to_string(result.metrics.expanded)+
   ",\"edge_visits\":"+std::to_string(result.metrics.edge_visits)+
   ",\"ripups\":"+std::to_string(result.metrics.ripups)+
   ",\"overused_resources\":"+std::to_string(result.metrics.overused_resources)+
   ",\"route_ms\":"+std::to_string(millis(begin,routed))+
   ",\"wall_ms\":"+std::to_string(millis(begin,end))+"}";
  std::ofstream report(output+".pathfinder.json");
  if(!report)throw std::runtime_error("cannot create "+output+".pathfinder.json");
  report<<json<<'\n';std::cout<<json<<'\n';
  return result.legal?0:3;
 }catch(const std::exception& error){std::cerr<<"error: "<<error.what()<<'\n';return 1;}
}
