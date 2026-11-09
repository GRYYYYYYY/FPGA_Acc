#include "globals.h"
#include "vpr_context.h"
#include "post_routing_pb_pin_fixup.h"
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <string>
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
extern "C" void real_sync(const Netlist<>& n,const DeviceContext& d,AtomContext& a,ClusteringContext& c,const PlacementContext& p,const bool& verbose) asm("__real__Z24sync_netlists_to_routingRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEERK13DeviceContextR11AtomContextR17ClusteringContextRK16PlacementContextRKb");
extern "C" void wrapped_sync(const Netlist<>& n,const DeviceContext& d,AtomContext& a,ClusteringContext& c,const PlacementContext& p,const bool& verbose) asm("__wrap__Z24sync_netlists_to_routingRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEERK13DeviceContextR11AtomContextR17ClusteringContextRK16PlacementContextRKb");
extern "C" void wrapped_sync(const Netlist<>& n,const DeviceContext& d,AtomContext& a,ClusteringContext& c,const PlacementContext& p,const bool& verbose){
 const char* prefix=std::getenv("ROUTECAST_SYNC_IDENTITY_PREFIX");
 if(prefix&&*prefix)capture((std::string(prefix)+".before.jsonl").c_str());
 real_sync(n,d,a,c,p,verbose);
 if(prefix&&*prefix)capture((std::string(prefix)+".after.jsonl").c_str());
}
