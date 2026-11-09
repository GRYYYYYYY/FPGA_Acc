#include "globals.h"
#include "vpr_context.h"
#include "post_routing_pb_pin_fixup.h"
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <string>
#include <tuple>
#include <charconv>
#include <sstream>
#include <limits>
#include <spawn.h>
#include <sys/wait.h>
#include <signal.h>
#include <unistd.h>
#include <chrono>
#include <thread>
extern char** environ;
#include "vtr_digest.h"
#include "read_route.h"
#include "check_route.h"
#include "route_common.h"
#include "vpr_api.h"
#include "output_clustering.h"
#include <filesystem>
#include <execinfo.h>
static bool defer_transaction=false;
static void capture(const char* output){
  std::ofstream f(output);if(!f)throw std::runtime_error("identity capture open failed");
  const auto& nets=g_vpr_ctx.clustering().clb_nlist;const auto& placement=g_vpr_ctx.placement();const auto& device=g_vpr_ctx.device();
  for(auto net:nets.nets()){
   f<<"{\"net_id\":"<<size_t(net)<<",\"name\":"<<std::quoted(nets.net_name(net))<<",\"pins\":[";bool first=true;
   for(auto pin:nets.net_pins(net)){
    auto block=nets.pin_block(pin);auto loc=placement.block_locs()[block].loc;int physical=placement.physical_pins()[pin];auto type=device.grid.get_physical_type({loc.x,loc.y,loc.layer});
    if(!first)f<<",";first=false;
    f<<"{\"index\":"<<nets.pin_net_index(pin)<<",\"block\":"<<std::quoted(nets.block_name(block))<<",\"port\":"<<std::quoted(nets.port_name(nets.pin_port(pin)))<<",\"bit\":"<<nets.pin_port_bit(pin)<<",\"physical_pin\":"<<physical<<",\"class\":"<<type->pin_class[physical]<<",\"x\":"<<loc.x<<",\"y\":"<<loc.y<<",\"layer\":"<<loc.layer<<"}";
   }
   f<<"]}\n";
  }
  f.close();if(!f)throw std::runtime_error("identity capture write failed");

}
static t_router_opts saved_opts;
static bool have_opts=false;
static uint64_t context_epoch=0;
static std::string loaded_graph_path;
static std::string actual_graph_cli_path(){
 std::ifstream f("/proc/self/cmdline",std::ios::binary);std::string token,path;unsigned matches=0;
 while(std::getline(f,token,'\0'))if(token=="--read_rr_graph"){if(!std::getline(f,path,'\0')||path.empty())throw std::runtime_error("missing native graph argument");++matches;}
 if(matches!=1)throw std::runtime_error("transaction requires exactly one native --read_rr_graph argument");return path;
}
static std::string loaded_graph_digest,loaded_net_digest,loaded_place_digest,loaded_arch_digest,parent_route_digest;
static uint64_t parse_epoch(const std::string& value){
 if(value.empty()||value.find_first_not_of("0123456789")!=std::string::npos)throw std::runtime_error("invalid epoch integer");
 uint64_t result=0;auto parsed=std::from_chars(value.data(),value.data()+value.size(),result);
 if(parsed.ec!=std::errc()||parsed.ptr!=value.data()+value.size())throw std::runtime_error("epoch overflow");return result;
}
static std::string validate_request(const char* manifest,const char* candidate){
 if(!have_opts||saved_opts.flat_routing||saved_opts.check_route!=e_check_route_option::FULL||saved_opts.reorder_rr_graph_nodes_algorithm!=DONT_REORDER)throw std::runtime_error("FULL nonflat loaded context required");
 if(!manifest||!*manifest)throw std::runtime_error("missing transaction request");
 std::ifstream f(manifest);std::string line;
 if(!std::getline(f,line)||line!="ROUTECAST_NATIVE_TX_V1")throw std::runtime_error("request version mismatch");
 auto field=[&](const char* key){std::string k,v,extra;if(!std::getline(f,line))throw std::runtime_error("truncated request");std::istringstream row(line);if(!(row>>k>>v)||row>>extra||k!=key)throw std::runtime_error("request field/order mismatch");return v;};
 auto expected=parse_epoch(field("epoch"));auto next=parse_epoch(field("next_epoch"));
 if(expected!=context_epoch||expected==std::numeric_limits<uint64_t>::max()||next!=expected+1)throw std::runtime_error("stale/invalid epoch transition");
 if(field("graph")!=loaded_graph_digest||vtr::secure_digest_file(loaded_graph_path)!=loaded_graph_digest)throw std::runtime_error("graph binding mismatch");
 if(field("net")!=loaded_net_digest||g_vpr_ctx.clustering().clb_nlist.netlist_id()!=loaded_net_digest)throw std::runtime_error("NET binding mismatch");
 if(field("placement")!=loaded_place_digest||g_vpr_ctx.placement().placement_id!=loaded_place_digest)throw std::runtime_error("placement binding mismatch");
 if(field("architecture")!=loaded_arch_digest||g_vpr_ctx.device().arch->architecture_id!=loaded_arch_digest)throw std::runtime_error("architecture binding mismatch");
 if(field("parent_route")!=parent_route_digest)throw std::runtime_error("parent route binding mismatch");
 auto digest=field("candidate");if(digest!=vtr::secure_digest_file(candidate))throw std::runtime_error("candidate binding mismatch");
 if(!std::getline(f,line)||line!="END"||std::getline(f,line))throw std::runtime_error("trailing/missing request END");return digest;
}
static std::string json_string(const std::string& value){
 std::ostringstream out;out<<'"';for(unsigned char c:value){if(c=='"'||c=='\\')out<<'\\'<<char(c);else if(c<32)out<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<int(c)<<std::dec;else out<<char(c);}out<<'"';return out.str();
}
extern "C" bool real_read(const char*,const t_router_opts&,bool,bool) asm("__real__Z10read_routePKcRK13t_router_optsbb");
extern "C" bool wrapped_read(const char*,const t_router_opts&,bool,bool) asm("__wrap__Z10read_routePKcRK13t_router_optsbb");
extern "C" bool wrapped_read(const char* path,const t_router_opts& opts,bool digests,bool flat){
 saved_opts=opts;have_opts=!flat;
 bool valid=real_read(path,opts,digests,flat);
 if(valid){loaded_graph_path=actual_graph_cli_path();loaded_graph_digest=vtr::secure_digest_file(loaded_graph_path);loaded_net_digest=g_vpr_ctx.clustering().clb_nlist.netlist_id();loaded_place_digest=g_vpr_ctx.placement().placement_id;loaded_arch_digest=g_vpr_ctx.device().arch->architecture_id;parent_route_digest=vtr::secure_digest_file(path);context_epoch=0;}
 return valid;
}
extern "C" void real_sync(const Netlist<>& n,const DeviceContext& d,AtomContext& a,ClusteringContext& c,const PlacementContext& p,const bool& verbose) asm("__real__Z24sync_netlists_to_routingRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEERK13DeviceContextR11AtomContextR17ClusteringContextRK16PlacementContextRKb");
extern "C" void wrapped_sync(const Netlist<>& n,const DeviceContext& d,AtomContext& a,ClusteringContext& c,const PlacementContext& p,const bool& verbose) asm("__wrap__Z24sync_netlists_to_routingRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEERK13DeviceContextR11AtomContextR17ClusteringContextRK16PlacementContextRKb");
extern "C" void wrapped_sync(const Netlist<>& n,const DeviceContext& d,AtomContext& a,ClusteringContext& c,const PlacementContext& p,const bool& verbose){
 if(defer_transaction){real_sync(n,d,a,c,p,verbose);return;}
 const char* prefix=std::getenv("ROUTECAST_SYNC_IDENTITY_PREFIX");
 if(prefix&&*prefix)capture((std::string(prefix)+".before.jsonl").c_str());
 const char* producer=std::getenv("ROUTECAST_TX_PRODUCER");
 if(producer&&*producer){
  const char* export_prefix=std::getenv("ROUTECAST_TX_EXPORT_PREFIX");
  if(!export_prefix||!*export_prefix||!have_opts||saved_opts.flat_routing||saved_opts.check_route!=e_check_route_option::FULL||saved_opts.reorder_rr_graph_nodes_algorithm!=DONT_REORDER)throw std::runtime_error("producer requires FULL loaded context and export prefix");
  std::string stem=export_prefix;
  auto& routing=g_vpr_ctx.mutable_routing();auto saved_id=routing.routing_id;
  print_route(n,"design.place",(stem+".route").c_str(),false);routing.routing_id=saved_id;
  capture((stem+".identity.jsonl").c_str());
  std::ofstream binding(stem+".binding.json");
  binding<<"{\"epoch\":"<<context_epoch<<",\"graph\":"<<json_string(loaded_graph_digest)<<",\"net\":"<<json_string(loaded_net_digest)<<",\"placement\":"<<json_string(loaded_place_digest)<<",\"architecture\":"<<json_string(loaded_arch_digest)<<",\"parent_route\":"<<json_string(parent_route_digest)<<",\"export_route\":"<<json_string(vtr::secure_digest_file(stem+".route"))<<",\"identity\":"<<json_string(vtr::secure_digest_file(stem+".identity.jsonl"))<<"}\n";
  binding.close();if(!binding)throw std::runtime_error("producer binding export failed");
  char* args[]={const_cast<char*>(producer),const_cast<char*>(export_prefix),nullptr};pid_t child;
  if(posix_spawn(&child,producer,nullptr,nullptr,args,environ)!=0)throw std::runtime_error("producer spawn failed");
  int status=0;auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(120);
  for(;;){auto result=waitpid(child,&status,WNOHANG);if(result==child)break;if(result<0)throw std::runtime_error("producer wait failed");if(std::chrono::steady_clock::now()>=deadline){kill(child,SIGKILL);waitpid(child,&status,0);throw std::runtime_error("producer timeout");}std::this_thread::sleep_for(std::chrono::milliseconds(20));}
  if(!WIFEXITED(status)||WEXITSTATUS(status)!=0)throw std::runtime_error("producer failed before import");
 }
 const char* candidate=std::getenv("ROUTECAST_TX_CANDIDATE");
 const char* txprefix=std::getenv("ROUTECAST_TX_PREFIX");
 if(candidate&&*candidate){
 if(!txprefix||!*txprefix)throw std::runtime_error("transaction output prefix required");
 std::string output_base=txprefix;
 const char* request=std::getenv("ROUTECAST_TX_REQUEST");
 int attempts=std::getenv("ROUTECAST_TX_TEST_REPLAY")?2:1;
 for(int attempt=0;attempt<attempts;++attempt){
 std::string stem=output_base+".attempt"+std::to_string(attempt);
 txprefix=stem.c_str();
  if(!have_opts||!txprefix||!*txprefix)throw std::runtime_error("transaction requires analysis-loaded nonflat context and output prefix");
  auto& r=g_vpr_ctx.mutable_routing();
  uint64_t epoch_before=context_epoch;std::string candidate_digest,guard_error;
  try{candidate_digest=validate_request(request,candidate);}catch(const std::exception& e){guard_error=e.what();}
  if(!guard_error.empty()){
   auto saved_id=r.routing_id;print_route(n,"design.place",(stem+".before.route").c_str(),false);r.routing_id=saved_id;
   print_route(n,"design.place",(stem+".after.route").c_str(),false);r.routing_id=saved_id;
   std::ofstream status(stem+".json");status<<"{\"committed\":false,\"mutation_started\":false,\"epoch_before\":"<<epoch_before<<",\"epoch_after\":"<<context_epoch<<",\"error\":"<<json_string(guard_error)<<"}\n";if(!status)throw std::runtime_error("guard status write failed");continue;
  }
  print_route(n,"design.place",(std::string(txprefix)+".before.route").c_str(),false);
  auto backup=std::make_tuple(std::move(r.route_trees),std::move(r.trace_nodes),std::move(r.net_rr_terminals),std::move(r.is_clock_net),std::move(r.rr_blk_source),std::move(r.rr_node_route_inf),std::move(r.net_terminal_groups),std::move(r.net_terminal_group_num),std::move(r.non_configurable_bitset),std::move(r.net_status),std::move(r.route_bb),std::move(r.clb_opins_used_locally),std::move(r.routing_id),std::move(r.is_flat));
  bool committed=false;std::string error;
  try{
   if(!real_read(candidate,saved_opts,true,false))throw std::runtime_error("candidate capacity infeasible");
   check_route(n,saved_opts.route_type,saved_opts.check_route,false);
   if(std::getenv("ROUTECAST_TX_FORCE_ROLLBACK"))throw std::runtime_error("forced post-validation rejection");
   if(vtr::secure_digest_file(candidate)!=candidate_digest)throw std::runtime_error("candidate changed during import");
   committed=true;context_epoch=epoch_before+1;parent_route_digest=candidate_digest;
  }catch(const std::exception& e){error=e.what();}
  catch(...){error="native candidate import exception";}
  if(!committed){
  r.route_trees=std::move(std::get<0>(backup));
  r.trace_nodes=std::move(std::get<1>(backup));
  r.net_rr_terminals=std::move(std::get<2>(backup));
  r.is_clock_net=std::move(std::get<3>(backup));
  r.rr_blk_source=std::move(std::get<4>(backup));
  r.rr_node_route_inf=std::move(std::get<5>(backup));
  r.net_terminal_groups=std::move(std::get<6>(backup));
  r.net_terminal_group_num=std::move(std::get<7>(backup));
  r.non_configurable_bitset=std::move(std::get<8>(backup));
  r.net_status=std::move(std::get<9>(backup));
  r.route_bb=std::move(std::get<10>(backup));
  r.clb_opins_used_locally=std::move(std::get<11>(backup));
  r.routing_id=std::move(std::get<12>(backup));
  r.is_flat=std::move(std::get<13>(backup));
   check_route(n,saved_opts.route_type,saved_opts.check_route,false);
  }
  print_route(n,"design.place",(std::string(txprefix)+".after.route").c_str(),false);
  std::ofstream status(std::string(txprefix)+".json");status<<"{\"committed\":"<<(committed?"true":"false")<<",\"mutation_started\":true,\"epoch_before\":"<<epoch_before<<",\"epoch_after\":"<<context_epoch<<",\"error\":"<<json_string(error)<<"}\n";
  if(!status)throw std::runtime_error("transaction status write failed");
 }
 }
 real_sync(n,d,a,c,p,verbose);
 if(prefix&&*prefix)capture((std::string(prefix)+".after.jsonl").c_str());
}

extern bool routecast_original_analysis_flow(const Netlist<>&,t_vpr_setup&,const t_arch&,const RouteStatus&,bool);
bool routecast_after_routing(const Netlist<>& n,t_vpr_setup& setup,const t_arch& arch,const RouteStatus& status,bool flat){
 if(std::getenv("ROUTECAST_TX_DEBUG_STACK")){auto debug_handler=[](int){void* stack[40];int count=backtrace(stack,40);backtrace_symbols_fd(stack,count,2);_exit(139);};signal(SIGSEGV,debug_handler);signal(SIGABRT,debug_handler);}
 if(!std::getenv("ROUTECAST_TX_POST_ROUTE"))return routecast_original_analysis_flow(n,setup,arch,status,flat);
 defer_transaction=true;bool result=routecast_original_analysis_flow(n,setup,arch,status,flat);defer_transaction=false;
 if(!result||!status.success()||flat||!setup.TimingEnabled)throw std::runtime_error("post-route transaction requires legal nonflat timing-analyzed route");
 const char* prefix=std::getenv("ROUTECAST_TX_EXPORT_PREFIX");if(!prefix||!*prefix)throw std::runtime_error("post-route export prefix required");
 std::filesystem::copy_file("report_timing.setup.rpt",std::string(prefix)+".initial.setup.rpt");
 saved_opts=setup.RouterOpts;have_opts=true;
 loaded_graph_path=actual_graph_cli_path();loaded_graph_digest=vtr::secure_digest_file(loaded_graph_path);loaded_net_digest=g_vpr_ctx.clustering().clb_nlist.netlist_id();loaded_place_digest=g_vpr_ctx.placement().placement_id;loaded_arch_digest=arch.architecture_id;context_epoch=0;
 auto& routing=g_vpr_ctx.mutable_routing();auto saved_id=routing.routing_id;std::string parent=std::string(prefix)+".parent.route";
 print_route(n,setup.FileNameOpts.PlaceFile.c_str(),parent.c_str(),false);routing.routing_id=saved_id;parent_route_digest=vtr::secure_digest_file(parent);
 wrapped_sync(n,g_vpr_ctx.device(),g_vpr_ctx.mutable_atom(),g_vpr_ctx.mutable_clustering(),g_vpr_ctx.placement(),setup.PackerOpts.pack_verbosity>2);
 print_route(n,setup.FileNameOpts.PlaceFile.c_str(),setup.FileNameOpts.RouteFile.c_str(),false);
 std::string packed=setup.PackerOpts.output_file+".post_routing";write_packing_results_to_xml(setup.PackerOpts.global_clocks,arch.architecture_id,packed.c_str());
 vpr_analysis(n,setup,arch,status,false);
 return result;
}
