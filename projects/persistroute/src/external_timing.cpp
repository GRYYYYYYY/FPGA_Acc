#include "external_timing.hpp"

#include <algorithm>
#include <cstdlib>
#include <fstream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <sys/wait.h>

namespace persistroute {
namespace {

std::string shell_quote(const std::string& text) {
 std::string out="'";
 for(const char ch:text)out+=ch=='\''?"'\\''":std::string(1,ch);
 return out+"'";
}

std::uint64_t path_delay_ps(const std::vector<Node>& nodes,const std::vector<Edge>& edges,
 const RoutedTask& routed) {
 if(!routed.routed)return 0;
 std::uint32_t source=routed.task.source;std::uint64_t delay=0;
 for(const auto sink:routed.path){
  if(source>=nodes.size()||sink>=nodes.size())throw std::runtime_error("timing path contains an invalid node");
  const Node node=nodes[source];bool found=false;std::uint16_t best=std::numeric_limits<std::uint16_t>::max();
  for(std::uint32_t i=0;i<node.edge_count;++i){const Edge& edge=edges.at(node.edge_begin+i);if(edge.dst==sink){best=std::min(best,edge.delay_q);found=true;}}
  if(!found)throw std::runtime_error("timing path contains a non-edge");
  delay+=best;source=sink;
 }
 return delay;
}

std::vector<std::string> split_csv(const std::string& line) {
 std::vector<std::string> fields;std::size_t begin=0;
 while(true){const auto comma=line.find(',',begin);fields.push_back(line.substr(begin,comma-begin));if(comma==std::string::npos)break;begin=comma+1;}
 return fields;
}

template<typename T>T parse_integer(const std::string& text,const char* field) {
 std::size_t used=0;
 try {
  if constexpr(std::numeric_limits<T>::is_signed){const long long value=std::stoll(text,&used,10);if(used!=text.size()||value<std::numeric_limits<T>::min()||value>std::numeric_limits<T>::max())throw std::out_of_range(field);return static_cast<T>(value);}
  else {if(!text.empty()&&text.front()=='-')throw std::out_of_range(field);const unsigned long long value=std::stoull(text,&used,10);if(used!=text.size()||value>std::numeric_limits<T>::max())throw std::out_of_range(field);return static_cast<T>(value);}
 }catch(const std::exception&){throw std::runtime_error(std::string("invalid timing analyzer ")+field+": "+text);}
}

} // namespace

TimingAnalyzer make_external_timing_analyzer(const std::string& command,const std::string& audit_prefix) {
 if(command.empty()||audit_prefix.empty())throw std::invalid_argument("external timing command/prefix must be non-empty");
 return [command,audit_prefix](std::uint32_t iteration,const std::vector<Node>& nodes,
   const std::vector<Edge>& edges,const std::vector<RoutedTask>& tasks) {
  const std::string stem=audit_prefix+".timing_iteration_"+std::to_string(iteration);
  const std::string input_path=stem+".input.csv",output_path=stem+".output.csv";
  std::ofstream input(input_path);if(!input)throw std::runtime_error("cannot create "+input_path);
  input<<"iteration,task_id,net_id,source,sink,routed,delay_ps,criticality_q\n";
  for(const auto& task:tasks)input<<iteration<<','<<task.task.id<<','<<task.task.net_id<<','
    <<task.task.source<<','<<task.task.sink<<','<<(task.routed?1:0)<<','
    <<path_delay_ps(nodes,edges,task)<<','<<task.task.criticality_q<<'\n';
  input.close();if(!input)throw std::runtime_error("failed writing "+input_path);
  const std::string invocation=command+" "+std::to_string(iteration)+" "+shell_quote(input_path)+" "+shell_quote(output_path);
  const int status=std::system(invocation.c_str());
  if(status==-1||!WIFEXITED(status)||WEXITSTATUS(status)!=0){std::ostringstream msg;msg<<"timing analyzer failed for iteration "<<iteration<<" (status "<<status<<')';throw std::runtime_error(msg.str());}
  std::ifstream output(output_path);if(!output)throw std::runtime_error("timing analyzer did not create "+output_path);
  std::string line;if(!std::getline(output,line)||line!="task_id,criticality_q,delay_ps,slack_ps,critical_path_delay_ps")throw std::runtime_error("bad timing analyzer CSV header");
  TimingAnalysisResult result;std::map<std::uint32_t,bool> ids;
  while(std::getline(output,line)){if(line.empty())continue;const auto fields=split_csv(line);if(fields.size()!=5)throw std::runtime_error("bad timing analyzer CSV row");TimingConnectionUpdate update;update.task_id=parse_integer<std::uint32_t>(fields[0],"task_id");update.criticality_q=parse_integer<std::uint16_t>(fields[1],"criticality_q");update.delay_ps=parse_integer<std::uint64_t>(fields[2],"delay_ps");update.slack_ps=parse_integer<std::int64_t>(fields[3],"slack_ps");const auto cpd=parse_integer<std::uint64_t>(fields[4],"critical_path_delay_ps");if(!ids.emplace(update.task_id,true).second)throw std::runtime_error("duplicate timing analyzer task ID");if(result.connections.empty())result.critical_path_delay_ps=cpd;else if(result.critical_path_delay_ps!=cpd)throw std::runtime_error("inconsistent timing analyzer critical path delay");result.connections.push_back(update);}
  return result;
 };
}

} // namespace persistroute
