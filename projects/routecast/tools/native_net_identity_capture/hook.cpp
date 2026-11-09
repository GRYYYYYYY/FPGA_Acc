#include "globals.h"
#include "vpr_context.h"
#include "read_route.h"
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <stdexcept>
extern "C" bool real_read(const char*,const t_router_opts&,bool,bool) asm("__real__Z10read_routePKcRK13t_router_optsbb");
extern "C" bool captured_read(const char*,const t_router_opts&,bool,bool) asm("__wrap__Z10read_routePKcRK13t_router_optsbb");
extern "C" bool captured_read(const char* path,const t_router_opts& opts,bool digests,bool flat){
 const char* output=std::getenv("ROUTECAST_NET_IDENTITY_FILE");
 if(output&&*output){
  if(flat)throw std::runtime_error("cluster identity capture rejects flat mode");
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
 return real_read(path,opts,digests,flat);
}
