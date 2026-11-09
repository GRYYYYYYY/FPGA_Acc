#include "globals.h"
#include "vpr_context.h"
#include "rr_graph.h"
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <stdexcept>
extern "C" void real_graph(t_graph_type,const std::vector<t_physical_tile_type>&,const DeviceGrid&,const t_chan_width&,t_det_routing_arch*,const std::vector<t_segment_inf>&,const t_router_opts&,const std::vector<t_direct_inf>&,int*,bool) asm("__real__Z15create_rr_graph12e_graph_typeRKSt6vectorI20t_physical_tile_typeSaIS1_EERK10DeviceGridRK12t_chan_widthP18t_det_routing_archRKS0_I13t_segment_infSaISE_EERK13t_router_optsRKS0_I12t_direct_infSaISM_EEPib");
extern "C" void captured_graph(t_graph_type,const std::vector<t_physical_tile_type>&,const DeviceGrid&,const t_chan_width&,t_det_routing_arch*,const std::vector<t_segment_inf>&,const t_router_opts&,const std::vector<t_direct_inf>&,int*,bool) asm("__wrap__Z15create_rr_graph12e_graph_typeRKSt6vectorI20t_physical_tile_typeSaIS1_EERK10DeviceGridRK12t_chan_widthP18t_det_routing_archRKS0_I13t_segment_infSaISE_EERK13t_router_optsRKS0_I12t_direct_infSaISM_EEPib");
#include "read_route.h"
extern "C" void captured_graph(t_graph_type kind,const std::vector<t_physical_tile_type>& types,const DeviceGrid& grid,const t_chan_width& width,t_det_routing_arch* arch,const std::vector<t_segment_inf>& segments,const t_router_opts& opts,const std::vector<t_direct_inf>& directs,int* warnings,bool flat){
 if(std::getenv("ROUTECAST_IDENTITY_ONLY")){
 const char* output=std::getenv("ROUTECAST_NET_IDENTITY_FILE");
 if(flat||opts.doRouting!=STAGE_LOAD||!output||!*output)throw std::runtime_error("identity-only requires clustered load stage and output");
 if(warnings)*warnings=0;return;
 }
 real_graph(kind,types,grid,width,arch,segments,opts,directs,warnings,flat);
}
extern "C" bool real_read(const char*,const t_router_opts&,bool,bool) asm("__real__Z10read_routePKcRK13t_router_optsbb");
extern "C" bool captured_read(const char*,const t_router_opts&,bool,bool) asm("__wrap__Z10read_routePKcRK13t_router_optsbb");
extern "C" bool captured_read(const char* path,const t_router_opts& opts,bool digests,bool flat){
 const char* output=std::getenv("ROUTECAST_NET_IDENTITY_FILE");
 if(std::getenv("ROUTECAST_IDENTITY_ONLY")){
  if(!output||!*output||opts.doRouting!=STAGE_LOAD)throw std::runtime_error("identity-only requires output and load stage");
  if(flat)throw std::runtime_error("cluster identity capture rejects flat mode");
  std::ofstream f(output);if(!f)throw std::runtime_error("identity capture open failed");
  const auto& nets=g_vpr_ctx.clustering().clb_nlist;const auto& placement=g_vpr_ctx.placement();const auto& device=g_vpr_ctx.device();
  for(auto net:nets.nets()){
   f<<"{\"net_id\":"<<size_t(net)<<",\"name\":"<<std::quoted(nets.net_name(net))<<",\"ignored\":"<<(nets.net_is_ignored(net)?"true":"false")<<",\"pins\":[";bool first=true;
   for(auto pin:nets.net_pins(net)){
    auto block=nets.pin_block(pin);auto loc=placement.block_locs()[block].loc;int physical=placement.physical_pins()[pin];auto type=device.grid.get_physical_type({loc.x,loc.y,loc.layer});
    if(!first)f<<",";first=false;
    f<<"{\"index\":"<<nets.pin_net_index(pin)<<",\"block\":"<<std::quoted(nets.block_name(block))<<",\"port\":"<<std::quoted(nets.port_name(nets.pin_port(pin)))<<",\"bit\":"<<nets.pin_port_bit(pin)<<",\"physical_pin\":"<<physical<<",\"class\":"<<type->pin_class[physical]<<",\"x\":"<<loc.x<<",\"y\":"<<loc.y<<",\"layer\":"<<loc.layer<<"}";
   }
   f<<"]}\n";
  }
  f.close();if(!f)throw std::runtime_error("identity capture write failed");
  std::ofstream phase(std::string(output)+".phase.json");phase<<"{\"phase\":\"after_placement_before_route_import\",\"rr_graph_skipped\":true,\"exit_code\":1}\n";phase.close();if(!phase)throw std::runtime_error("phase write failed");std::exit(1);
 }
 return real_read(path,opts,digests,flat);
}
