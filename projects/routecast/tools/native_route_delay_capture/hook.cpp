#include "globals.h"
#include "vpr_context.h"
#include "read_route.h"
#include <cstdlib>
#include <cstdio>
#include <string>
#include <stdexcept>
using Nets = Netlist<>;
void print_route(const Nets&,FILE*,bool);
extern "C" void real_sync(const Nets&,const DeviceContext&,AtomContext&,ClusteringContext&,const PlacementContext&,const bool&) asm("__real__Z24sync_netlists_to_routingRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEERK13DeviceContextR11AtomContextR17ClusteringContextRK16PlacementContextRKb");
extern "C" void wrapped_sync(const Nets&,const DeviceContext&,AtomContext&,ClusteringContext&,const PlacementContext&,const bool&) asm("__wrap__Z24sync_netlists_to_routingRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEERK13DeviceContextR11AtomContextR17ClusteringContextRK16PlacementContextRKb");
static void capture(const Nets& nets,const char* dir,const char* label){
 if(!dir||!*dir)return;
 std::string path=std::string(dir)+"/"+label+".route";
 FILE* file=std::fopen(path.c_str(),"w");if(!file)throw std::runtime_error("native route capture open failed");
 print_route(nets,file,false);if(std::fclose(file))throw std::runtime_error("native route capture close failed");
 path=std::string(dir)+"/"+label+".delays.tsv";
 file=std::fopen(path.c_str(),"w");if(!file)throw std::runtime_error("delay capture open failed");
 std::fprintf(file,"net\tname\tnode\tpin\tdelay_s\tR_upstream\tC_downstream\n");
 const auto& routing=g_vpr_ctx.routing();
 for(auto net:nets.nets()) if(routing.route_trees[net]) for(const auto& node:routing.route_trees[net]->all_nodes())
  std::fprintf(file,"%zu\t%s\t%zu\t%d\t%.9g\t%.9g\t%.9g\n",size_t(net),nets.net_name(net).c_str(),size_t(node.inode),node.net_pin_index,double(node.Tdel),double(node.R_upstream),double(node.C_downstream));
 if(std::fclose(file))throw std::runtime_error("delay capture close failed");

}
extern "C" void wrapped_sync(const Nets& nets,const DeviceContext& device,AtomContext& atom,ClusteringContext& clustering,const PlacementContext& placement,const bool& verbose){
 const char* dir=std::getenv("ROUTECAST_SYNC_CAPTURE_DIR");capture(nets,dir,"before_sync");
 real_sync(nets,device,atom,clustering,placement,verbose);capture(nets,dir,"after_sync");
}
