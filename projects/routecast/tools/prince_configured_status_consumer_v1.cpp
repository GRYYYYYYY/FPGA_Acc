// Observation only after original print_route returns; no stop or native mutation.
#include "vpr_context.h"
#include "globals.h"
#include "route_utils.h"
#include "route.h"
#include "vtr_digest.h"
#include <sstream>
#include <iomanip>
#include <type_traits>
#include "prince_live_view_v2.h"
#include <fstream>
#include <chrono>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <cstdint>
#include <stdexcept>
#include <cmath>
#include <algorithm>
static int phase_iteration=0;static float phase_pres=0;static uint64_t phase_overused=0,phase_total=0,phase_worst=0;static int phase_updated=0;static float phase_timing[4]={};
static void consume_boundary(int);
extern "C" void SREAL(int,double,float,int,const RouterStats&,const OveruseInfo&,const WirelengthInfo&,std::shared_ptr<const SetupHoldTimingInfo>,float);
extern "C" void SWRAP(int i,double elapsed,float pres,int updated,const RouterStats& stats,const OveruseInfo& over,const WirelengthInfo& wire,std::shared_ptr<const SetupHoldTimingInfo> timing,float estimate){
 SREAL(i,elapsed,pres,updated,stats,over,wire,timing,estimate);
 phase_iteration=i;phase_pres=pres;phase_overused=over.overused_nodes;phase_total=over.total_overuse;phase_worst=over.worst_overuse;phase_updated=updated;
 if(!timing)throw std::runtime_error("missing timing context");
 phase_timing[0]=timing->setup_total_negative_slack();phase_timing[1]=timing->setup_worst_negative_slack();phase_timing[2]=timing->hold_total_negative_slack();phase_timing[3]=timing->hold_worst_negative_slack();
 consume_boundary(i);
}
extern "C" void REAL(const Netlist<>&,const char*,const char*,bool);
static uint64_t stamp(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
template<class T> static void put(std::ofstream& f,T x){f.write(reinterpret_cast<const char*>(&x),sizeof(x));}
static void capture_boundary(int iteration){
 auto begin=stamp();auto printed=begin;const char* directory=std::getenv("ROUTECAST_RESIDENT_BOUNDARY_DIR");if(!directory)return;
 if(phase_iteration!=iteration)throw std::runtime_error("boundary phase iteration mismatch");
 const auto& device=g_vpr_ctx.device();const auto& routing=g_vpr_ctx.routing();
 std::string path=std::string(directory)+"/iteration_"+std::to_string(iteration)+".bin";std::ofstream f(path,std::ios::binary);if(!f)throw std::runtime_error("boundary output open");
 f.write("RCBND001",8);put<uint64_t>(f,iteration);put<uint64_t>(f,device.rr_graph.num_nodes());
 for(auto node:device.rr_graph.nodes()){
  uint32_t bits;float value=routing.rr_node_route_inf[node].acc_cost;std::memcpy(&bits,&value,4);
  put<uint64_t>(f,size_t(node));put<uint32_t>(f,uint32_t(device.rr_graph.node_type(node)));put<int32_t>(f,routing.rr_node_route_inf[node].occ());put<int32_t>(f,device.rr_graph.node_capacity(node));put<uint32_t>(f,bits);
 }
 f.close();if(!f)throw std::runtime_error("boundary output write");auto captured=stamp();
 std::ofstream boxes(std::string(directory)+"/boxes_"+std::to_string(iteration)+".bin",std::ios::binary);boxes.write("RCBOX001",8);put<uint64_t>(boxes,iteration);put<uint64_t>(boxes,routing.route_bb.size());
 for(auto netid:routing.route_bb.keys()){const auto& b=routing.route_bb[netid];put<uint64_t>(boxes,size_t(netid));put<int32_t>(boxes,b.xmin);put<int32_t>(boxes,b.xmax);put<int32_t>(boxes,b.ymin);put<int32_t>(boxes,b.ymax);put<int32_t>(boxes,b.layer_min);put<int32_t>(boxes,b.layer_max);}boxes.close();if(!boxes)throw std::runtime_error("box write");
 uint32_t pres_bits;std::memcpy(&pres_bits,&phase_pres,4);std::ofstream phase(std::string(directory)+"/phase.tsv",std::ios::app);phase<<iteration<<'\t'<<pres_bits<<'\t'<<phase_overused<<'\t'<<phase_total<<'\t'<<phase_worst<<'\t'<<phase_updated;for(float value:phase_timing){uint32_t bits;std::memcpy(&bits,&value,4);phase<<'\t'<<bits;}phase<<'\n';if(!phase)throw std::runtime_error("phase write");
 std::ofstream meta(std::string(directory)+"/boundary_times.tsv",std::ios::app);meta<<iteration<<'\t'<<device.rr_graph.num_nodes()<<'\t'<<begin<<'\t'<<printed<<'\t'<<captured<<'\n';if(!meta)throw std::runtime_error("boundary metadata write");
}

static void hash_bytes(uint64_t& h,const void* ptr,size_t n){const auto* p=static_cast<const unsigned char*>(ptr);for(size_t i=0;i<n;++i){h^=p[i];h*=1099511628211ULL;}}
template<class T> static void hash_word(uint64_t& h,T x){hash_bytes(h,&x,sizeof(x));}
static void probe_view(int iteration,uint64_t expected_rr,uint64_t expected_bb,const char* ledger){
 using namespace routecast_live;static Mapping mapping(std::getenv("ROUTECAST_LIVE_NET_MAP"),std::getenv("ROUTECAST_LIVE_IDENTITY"));static std::unique_ptr<View> prior;Scope scope(mapping,iteration);auto view=scope.view();auto expected=mapping.identity;expected.iteration=iteration;view.require(expected);int identity_rejected=0,expired_rejected=0;
 if(prior){try{prior->rr(0);throw std::runtime_error("old view accepted");}catch(const std::logic_error&){++expired_rejected;}}
 for(int field=0;field<9;++field){auto bad=expected;switch(field){case 0:bad.graph[0]=bad.graph[0]=='0'?'1':'0';break;case 1:bad.netlist[0]=bad.netlist[0]=='0'?'1':'0';break;case 2:bad.placement[0]=bad.placement[0]=='0'?'1':'0';break;case 3:bad.binary[0]=bad.binary[0]=='0'?'1':'0';break;case 4:bad.phase="wrong_phase";break;case 5:++bad.iteration;break;case 6:bad.case_tag="wrong_case";break;case 7:bad.launch_config[0]=bad.launch_config[0]=='0'?'1':'0';break;case 8:bad.resolved_config[0]=bad.resolved_config[0]=='0'?'1':'0';break;}try{view.require(bad);throw std::runtime_error("wrong identity accepted");}catch(const std::logic_error&){++identity_rejected;}}
 uint64_t rh=14695981039346656037ULL,bh=rh;for(size_t n=0;n<view.node_count();++n){auto rr=view.rr(n);hash_word<uint64_t>(rh,n);hash_word<uint32_t>(rh,rr.kind);hash_word<int32_t>(rh,rr.occupancy);hash_word<int32_t>(rh,rr.capacity);hash_word<uint32_t>(rh,rr.acc_bits);}
 for(size_t n=0;n<view.net_count();++n){auto net=view.net(n);auto box=view.box(net.endpoint);if(box.native!=net.native)throw std::runtime_error("native endpoint join");hash_word<uint64_t>(bh,box.native);for(auto x:box.coordinates)hash_word<int32_t>(bh,x);}
 if(rh!=expected_rr||bh!=expected_bb)throw std::runtime_error("view state mismatch");bool foreign_rejected=false;std::thread foreign([&](){try{view.rr(0);}catch(const std::logic_error&){foreign_rejected=true;}});foreign.join();if(!foreign_rejected)throw std::runtime_error("foreign thread view accepted");
 prior.reset(new View(view));scope.close();for(int field=0;field<4;++field){try{switch(field){case 0:view.rr(0);break;case 1:view.net(0);break;case 2:view.box(0);break;case 3:view.identity();break;}throw std::runtime_error("expired view accepted");}catch(const std::logic_error&){++expired_rejected;}}
 std::ofstream out(std::string(ledger)+".view.tsv",std::ios::app);out<<iteration<<'\t'<<mapping.entries.size()<<'\t'<<identity_rejected<<'\t'<<expired_rejected<<'\t'<<foreign_rejected<<'\t'<<rh<<'\t'<<bh<<'\n';if(!out)throw std::runtime_error("view ledger write");
}
static void consume_boundary(int iteration){
 const char* path=std::getenv("ROUTECAST_RESIDENT_CALLBACK_FILE");if(!path)return;
 auto begin=stamp();const auto& device=g_vpr_ctx.device();const auto& routing=g_vpr_ctx.routing();uint64_t rh=14695981039346656037ULL,bh=rh,count=0,total=0,worst=0,elevated=0,channel_elevated=0;
 for(auto node:device.rr_graph.nodes()){
  const auto& state=routing.rr_node_route_inf[node];int32_t occ=state.occ(),cap=device.rr_graph.node_capacity(node);float acc=state.acc_cost;uint32_t bits;std::memcpy(&bits,&acc,4);uint32_t kind=uint32_t(device.rr_graph.node_type(node));
  if(occ<0||cap<=0||!std::isfinite(acc)||acc<1)throw std::runtime_error("consumer RR domain");
  uint64_t over=occ>cap?uint64_t(occ-cap):0;count+=over>0;total+=over;worst=std::max(worst,over);elevated+=acc>1;channel_elevated+=(kind==4||kind==5)&&acc>1;
  hash_word<uint64_t>(rh,size_t(node));hash_word<uint32_t>(rh,kind);hash_word<int32_t>(rh,occ);hash_word<int32_t>(rh,cap);hash_word<uint32_t>(rh,bits);
 }
 for(auto net:routing.route_bb.keys()){const auto& b=routing.route_bb[net];if(b.xmin<0||b.xmin>b.xmax||b.ymin<0||b.ymin>b.ymax||b.layer_min<0||b.layer_min>b.layer_max)throw std::runtime_error("consumer box domain");hash_word<uint64_t>(bh,size_t(net));for(int v:{b.xmin,b.xmax,b.ymin,b.ymax,b.layer_min,b.layer_max})hash_word<int32_t>(bh,v);}
 if(iteration!=phase_iteration||count!=phase_overused||total!=phase_total||worst!=phase_worst)throw std::runtime_error("consumer phase/overuse mismatch");
 probe_view(iteration,rh,bh,path);
 auto consumed=stamp();capture_boundary(iteration);auto captured=stamp();uint32_t pres_bits;std::memcpy(&pres_bits,&phase_pres,4);std::ofstream f(path,std::ios::app);f<<iteration<<'\t'<<device.rr_graph.num_nodes()<<'\t'<<routing.route_bb.size()<<'\t'<<pres_bits<<'\t'<<count<<'\t'<<total<<'\t'<<worst<<'\t'<<rh<<'\t'<<bh<<'\t'<<elevated<<'\t'<<channel_elevated<<'\t'<<begin<<'\t'<<consumed<<'\t'<<captured<<'\n';if(!f)throw std::runtime_error("callback ledger write");
}
extern "C" void WRAP(const Netlist<>& net,const char* place,const char* route,bool flat){REAL(net,place,route,flat);}

static std::string active_config;
namespace routecast_live {std::string active_configuration_digest(){if(active_config.empty())throw std::runtime_error("no active native configuration");return active_config;}}
static void cfg(std::ostream& s,const char* name,float x){uint32_t bits;std::memcpy(&bits,&x,4);s<<name<<"\tf32\t"<<bits<<'\n';}
static void cfg(std::ostream& s,const char* name,const std::string& x){s<<name<<"\tbytes\t";static const char digits[]="0123456789abcdef";for(unsigned char c:x)s<<digits[c>>4]<<digits[c&15];s<<'\n';}
template<class T> static void cfg(std::ostream& s,const char* name,T x){s<<name<<"\tinteger\t"<<static_cast<long long>(x)<<'\n';}
extern "C" bool RREAL(const Netlist<>&,int,const t_router_opts&,const t_analysis_opts&,t_det_routing_arch*,std::vector<t_segment_inf>&,NetPinsMatrix<float>&,std::shared_ptr<SetupHoldTimingInfo>,std::shared_ptr<RoutingDelayCalculator>,t_chan_width_dist,const std::vector<t_direct_inf>&,ScreenUpdatePriority,bool);
extern "C" bool RWRAP(const Netlist<>& nets,int width,const t_router_opts& router,const t_analysis_opts& analysis,t_det_routing_arch* arch,std::vector<t_segment_inf>& segments,NetPinsMatrix<float>& delays,std::shared_ptr<SetupHoldTimingInfo> timing,std::shared_ptr<RoutingDelayCalculator> calculator,t_chan_width_dist widths,const std::vector<t_direct_inf>& directs,ScreenUpdatePriority priority,bool flat){
 std::ostringstream s;s<<"ROUTECAST_NATIVE_RESOLVED_CONFIGURATION_V1\n";cfg(s,"width_fac",width);cfg(s,"flat_argument",flat);
 cfg(s,"t_router_opts.read_rr_edge_metadata",router.read_rr_edge_metadata);
 cfg(s,"t_router_opts.do_check_rr_graph",router.do_check_rr_graph);
 cfg(s,"t_router_opts.first_iter_pres_fac",router.first_iter_pres_fac);
 cfg(s,"t_router_opts.initial_pres_fac",router.initial_pres_fac);
 cfg(s,"t_router_opts.pres_fac_mult",router.pres_fac_mult);
 cfg(s,"t_router_opts.max_pres_fac",router.max_pres_fac);
 cfg(s,"t_router_opts.acc_fac",router.acc_fac);
 cfg(s,"t_router_opts.bend_cost",router.bend_cost);
 cfg(s,"t_router_opts.max_router_iterations",router.max_router_iterations);
 cfg(s,"t_router_opts.min_incremental_reroute_fanout",router.min_incremental_reroute_fanout);
 cfg(s,"t_router_opts.incr_reroute_delay_ripup",router.incr_reroute_delay_ripup);
 cfg(s,"t_router_opts.bb_factor",router.bb_factor);
 cfg(s,"t_router_opts.route_type",router.route_type);
 cfg(s,"t_router_opts.fixed_channel_width",router.fixed_channel_width);
 cfg(s,"t_router_opts.min_channel_width_hint",router.min_channel_width_hint);
 cfg(s,"t_router_opts.router_algorithm",router.router_algorithm);
 cfg(s,"t_router_opts.base_cost_type",router.base_cost_type);
 cfg(s,"t_router_opts.astar_fac",router.astar_fac);
 cfg(s,"t_router_opts.astar_offset",router.astar_offset);
 cfg(s,"t_router_opts.router_profiler_astar_fac",router.router_profiler_astar_fac);
 cfg(s,"t_router_opts.max_criticality",router.max_criticality);
 cfg(s,"t_router_opts.criticality_exp",router.criticality_exp);
 cfg(s,"t_router_opts.init_wirelength_abort_threshold",router.init_wirelength_abort_threshold);
 cfg(s,"t_router_opts.verify_binary_search",router.verify_binary_search);
 cfg(s,"t_router_opts.full_stats",router.full_stats);
 cfg(s,"t_router_opts.congestion_analysis",router.congestion_analysis);
 cfg(s,"t_router_opts.fanout_analysis",router.fanout_analysis);
 cfg(s,"t_router_opts.switch_usage_analysis",router.switch_usage_analysis);
 cfg(s,"t_router_opts.doRouting",router.doRouting);
 cfg(s,"t_router_opts.routing_failure_predictor",router.routing_failure_predictor);
 cfg(s,"t_router_opts.routing_budgets_algorithm",router.routing_budgets_algorithm);
 cfg(s,"t_router_opts.save_routing_per_iteration",router.save_routing_per_iteration);
 cfg(s,"t_router_opts.congested_routing_iteration_threshold_frac",router.congested_routing_iteration_threshold_frac);
 cfg(s,"t_router_opts.route_bb_update",router.route_bb_update);
 cfg(s,"t_router_opts.clock_modeling",router.clock_modeling);
 cfg(s,"t_router_opts.two_stage_clock_routing",router.two_stage_clock_routing);
 cfg(s,"t_router_opts.high_fanout_threshold",router.high_fanout_threshold);
 cfg(s,"t_router_opts.high_fanout_max_slope",router.high_fanout_max_slope);
 cfg(s,"t_router_opts.router_debug_net",router.router_debug_net);
 cfg(s,"t_router_opts.router_debug_sink_rr",router.router_debug_sink_rr);
 cfg(s,"t_router_opts.router_debug_iteration",router.router_debug_iteration);
 cfg(s,"t_router_opts.lookahead_type",router.lookahead_type);
 cfg(s,"t_router_opts.max_convergence_count",router.max_convergence_count);
 cfg(s,"t_router_opts.route_verbosity",router.route_verbosity);
 cfg(s,"t_router_opts.reconvergence_cpd_threshold",router.reconvergence_cpd_threshold);
 cfg(s,"t_router_opts.initial_timing",router.initial_timing);
 cfg(s,"t_router_opts.update_lower_bound_delays",router.update_lower_bound_delays);
 cfg(s,"t_router_opts.first_iteration_timing_report_file",router.first_iteration_timing_report_file);
 cfg(s,"t_router_opts.strict_checks",router.strict_checks);
 cfg(s,"t_router_opts.write_router_lookahead",router.write_router_lookahead);
 cfg(s,"t_router_opts.read_router_lookahead",router.read_router_lookahead);
 cfg(s,"t_router_opts.write_intra_cluster_router_lookahead",router.write_intra_cluster_router_lookahead);
 cfg(s,"t_router_opts.read_intra_cluster_router_lookahead",router.read_intra_cluster_router_lookahead);
 cfg(s,"t_router_opts.router_heap",router.router_heap);
 cfg(s,"t_router_opts.exit_after_first_routing_iteration",router.exit_after_first_routing_iteration);
 cfg(s,"t_router_opts.check_route",router.check_route);
 cfg(s,"t_router_opts.timing_update_type",router.timing_update_type);
 cfg(s,"t_router_opts.max_logged_overused_rr_nodes",router.max_logged_overused_rr_nodes);
 cfg(s,"t_router_opts.generate_rr_node_overuse_report",router.generate_rr_node_overuse_report);
 cfg(s,"t_router_opts.flat_routing",router.flat_routing);
 cfg(s,"t_router_opts.has_choke_point",router.has_choke_point);
 cfg(s,"t_router_opts.custom_3d_sb_fanin_fanout",router.custom_3d_sb_fanin_fanout);
 cfg(s,"t_router_opts.with_timing_analysis",router.with_timing_analysis);
 cfg(s,"t_router_opts.reorder_rr_graph_nodes_algorithm",router.reorder_rr_graph_nodes_algorithm);
 cfg(s,"t_router_opts.reorder_rr_graph_nodes_threshold",router.reorder_rr_graph_nodes_threshold);
 cfg(s,"t_router_opts.reorder_rr_graph_nodes_seed",router.reorder_rr_graph_nodes_seed);
 cfg(s,"t_analysis_opts.doAnalysis",analysis.doAnalysis);
 cfg(s,"t_analysis_opts.gen_post_synthesis_netlist",analysis.gen_post_synthesis_netlist);
 cfg(s,"t_analysis_opts.gen_post_implementation_merged_netlist",analysis.gen_post_implementation_merged_netlist);
 cfg(s,"t_analysis_opts.post_synth_netlist_unconn_input_handling",analysis.post_synth_netlist_unconn_input_handling);
 cfg(s,"t_analysis_opts.post_synth_netlist_unconn_output_handling",analysis.post_synth_netlist_unconn_output_handling);
 cfg(s,"t_analysis_opts.timing_report_npaths",analysis.timing_report_npaths);
 cfg(s,"t_analysis_opts.timing_report_detail",analysis.timing_report_detail);
 cfg(s,"t_analysis_opts.timing_report_skew",analysis.timing_report_skew);
 cfg(s,"t_analysis_opts.echo_dot_timing_graph_node",analysis.echo_dot_timing_graph_node);
 cfg(s,"t_analysis_opts.write_timing_summary",analysis.write_timing_summary);
 cfg(s,"t_analysis_opts.timing_update_type",analysis.timing_update_type);
 std::string text=s.str();std::istringstream input(text);std::string digest=vtr::secure_digest_stream(input);if(digest.rfind("SHA256:",0)!=0)throw std::runtime_error("configuration digest algorithm");digest=digest.substr(7);const char* path=std::getenv("ROUTECAST_RESIDENT_CALLBACK_FILE");if(path){std::ofstream f(std::string(path)+".resolved.tsv");f<<text;std::ofstream g(std::string(path)+".resolved.sha256",std::ios::app);g<<digest<<'\n';if(!f||!g)throw std::runtime_error("configuration output");}
 struct Reset {std::string previous;~Reset(){active_config=std::move(previous);}} reset{active_config};active_config=digest;return RREAL(nets,width,router,analysis,arch,segments,delays,timing,calculator,widths,directs,priority,flat);
}
