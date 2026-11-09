#include "globals.h"
#include "vpr_context.h"
#include "read_route.h"
#include "atom_lookup.h"
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <stdexcept>
extern "C" bool real_read(const char*,const t_router_opts&,bool,bool) asm("__real__Z10read_routePKcRK13t_router_optsbb");
extern "C" bool captured_read(const char*,const t_router_opts&,bool,bool) asm("__wrap__Z10read_routePKcRK13t_router_optsbb");
extern "C" bool captured_read(const char* path,const t_router_opts& opts,bool digests,bool flat){
 bool result=real_read(path,opts,digests,flat);
 const char* output=std::getenv("ROUTECAST_ATOM_TIMING_IDENTITY_FILE");
 if(result&&output&&*output){
  if(flat)throw std::runtime_error("atom timing identity rejects flat mode");
  std::ofstream f(output);if(!f)throw std::runtime_error("identity open failed");
  const auto& atom=g_vpr_ctx.atom();const auto& nets=atom.nlist;const auto& clusters=g_vpr_ctx.clustering().clb_nlist;
  for(auto pin:nets.pins()){
   auto block=nets.pin_block(pin);auto cluster=atom.lookup.atom_clb(block);auto net=nets.pin_net(pin);
   for(auto mode:{BlockTnode::EXTERNAL,BlockTnode::INTERNAL}){
    auto node=atom.lookup.atom_pin_tnode(pin,mode);
    f<<"{\"atom_pin_id\":"<<size_t(pin)<<",\"node_id\":";
    if(node)f<<size_t(node);else f<<"null";
    f<<",\"mode\":"<<std::quoted(mode==BlockTnode::EXTERNAL?"EXTERNAL":"INTERNAL")<<",\"atom\":"<<std::quoted(nets.block_name(block))<<",\"port\":"<<std::quoted(nets.port_name(nets.pin_port(pin)))<<",\"bit\":"<<nets.pin_port_bit(pin)<<",\"net\":"<<std::quoted(net?nets.net_name(net):"")<<",\"cluster\":"<<std::quoted(cluster?clusters.block_name(cluster):"")<<"}\n";
   }
  }
  f.close();if(!f)throw std::runtime_error("identity write failed");
 }
 return result;
}
