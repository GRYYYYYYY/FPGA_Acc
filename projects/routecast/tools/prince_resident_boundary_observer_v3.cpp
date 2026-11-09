// Observation only after original print_route returns; no stop or native mutation.
#include "vpr_context.h"
#include "globals.h"
#include "route_utils.h"
#include <fstream>
#include <chrono>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <cstdint>
#include <stdexcept>
static int phase_iteration=0;static float phase_pres=0;static uint64_t phase_overused=0,phase_total=0,phase_worst=0;static int phase_updated=0;static float phase_timing[4]={};
extern "C" void SREAL(int,double,float,int,const RouterStats&,const OveruseInfo&,const WirelengthInfo&,std::shared_ptr<const SetupHoldTimingInfo>,float);
extern "C" void SWRAP(int i,double elapsed,float pres,int updated,const RouterStats& stats,const OveruseInfo& over,const WirelengthInfo& wire,std::shared_ptr<const SetupHoldTimingInfo> timing,float estimate){
 SREAL(i,elapsed,pres,updated,stats,over,wire,timing,estimate);
 phase_iteration=i;phase_pres=pres;phase_overused=over.overused_nodes;phase_total=over.total_overuse;phase_worst=over.worst_overuse;phase_updated=updated;
 if(!timing)throw std::runtime_error("missing timing context");
 phase_timing[0]=timing->setup_total_negative_slack();phase_timing[1]=timing->setup_worst_negative_slack();phase_timing[2]=timing->hold_total_negative_slack();phase_timing[3]=timing->hold_worst_negative_slack();
}
extern "C" void REAL(const Netlist<>&,const char*,const char*,bool);
static uint64_t stamp(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
template<class T> static void put(std::ofstream& f,T x){f.write(reinterpret_cast<const char*>(&x),sizeof(x));}
extern "C" void WRAP(const Netlist<>& net,const char* place,const char* route,bool flat){
 auto begin=stamp();REAL(net,place,route,flat);auto printed=stamp();
 const char* directory=std::getenv("ROUTECAST_RESIDENT_BOUNDARY_DIR");int iteration=0;int consumed=0;
 if(!directory||!route||std::sscanf(route,"iteration_%d.route%n",&iteration,&consumed)!=1||consumed!=int(std::strlen(route)))return;
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
