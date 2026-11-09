// Observation only after original print_route returns; no stop or native mutation.
#include "vpr_context.h"
#include <fstream>
#include <chrono>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <cstdint>
#include <stdexcept>
extern "C" void REAL(const Netlist<>&,const char*,const char*,bool);
static uint64_t stamp(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
template<class T> static void put(std::ofstream& f,T x){f.write(reinterpret_cast<const char*>(&x),sizeof(x));}
extern "C" void WRAP(const Netlist<>& net,const char* place,const char* route,bool flat){
 auto begin=stamp();REAL(net,place,route,flat);auto printed=stamp();
 const char* directory=std::getenv("ROUTECAST_RESIDENT_BOUNDARY_DIR");int iteration=0;int consumed=0;
 if(!directory||!route||std::sscanf(route,"iteration_%d.route%n",&iteration,&consumed)!=1||consumed!=int(std::strlen(route)))return;
 const auto& device=g_vpr_ctx.device();const auto& routing=g_vpr_ctx.routing();
 std::string path=std::string(directory)+"/iteration_"+std::to_string(iteration)+".bin";std::ofstream f(path,std::ios::binary);if(!f)throw std::runtime_error("boundary output open");
 f.write("RCBND001",8);put<uint64_t>(f,iteration);put<uint64_t>(f,device.rr_graph.num_nodes());
 for(auto node:device.rr_graph.nodes()){
  uint32_t bits;float value=routing.rr_node_route_inf[node].acc_cost;std::memcpy(&bits,&value,4);
  put<uint64_t>(f,size_t(node));put<uint32_t>(f,uint32_t(device.rr_graph.node_type(node)));put<int32_t>(f,routing.rr_node_route_inf[node].occ());put<int32_t>(f,device.rr_graph.node_capacity(node));put<uint32_t>(f,bits);
 }
 f.close();if(!f)throw std::runtime_error("boundary output write");auto captured=stamp();
 std::ofstream meta(std::string(directory)+"/boundary_times.tsv",std::ios::app);meta<<iteration<<'\t'<<device.rr_graph.num_nodes()<<'\t'<<begin<<'\t'<<printed<<'\t'<<captured<<'\n';if(!meta)throw std::runtime_error("boundary metadata write");
}
