#include "globals.h"
#include "vpr_context.h"
#include "post_routing_pb_pin_fixup.h"
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <string>
#include <tuple>
#include "read_route.h"
#include "check_route.h"
#include "route_common.h"
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
extern "C" bool real_read(const char*,const t_router_opts&,bool,bool) asm("__real__Z10read_routePKcRK13t_router_optsbb");
extern "C" bool wrapped_read(const char*,const t_router_opts&,bool,bool) asm("__wrap__Z10read_routePKcRK13t_router_optsbb");
extern "C" bool wrapped_read(const char* path,const t_router_opts& opts,bool digests,bool flat){
 saved_opts=opts;have_opts=!flat;
 return real_read(path,opts,digests,flat);
}
extern "C" void real_sync(const Netlist<>& n,const DeviceContext& d,AtomContext& a,ClusteringContext& c,const PlacementContext& p,const bool& verbose) asm("__real__Z24sync_netlists_to_routingRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEERK13DeviceContextR11AtomContextR17ClusteringContextRK16PlacementContextRKb");
extern "C" void wrapped_sync(const Netlist<>& n,const DeviceContext& d,AtomContext& a,ClusteringContext& c,const PlacementContext& p,const bool& verbose) asm("__wrap__Z24sync_netlists_to_routingRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEERK13DeviceContextR11AtomContextR17ClusteringContextRK16PlacementContextRKb");
extern "C" void wrapped_sync(const Netlist<>& n,const DeviceContext& d,AtomContext& a,ClusteringContext& c,const PlacementContext& p,const bool& verbose){
 const char* prefix=std::getenv("ROUTECAST_SYNC_IDENTITY_PREFIX");
 if(prefix&&*prefix)capture((std::string(prefix)+".before.jsonl").c_str());
 const char* candidate=std::getenv("ROUTECAST_TX_CANDIDATE");
 const char* txprefix=std::getenv("ROUTECAST_TX_PREFIX");
 if(candidate&&*candidate){
  if(!have_opts||!txprefix||!*txprefix)throw std::runtime_error("transaction requires analysis-loaded nonflat context and output prefix");
  auto& r=g_vpr_ctx.mutable_routing();
  print_route(n,"design.place",(std::string(txprefix)+".before.route").c_str(),false);
  auto backup=std::make_tuple(std::move(r.route_trees),std::move(r.trace_nodes),std::move(r.net_rr_terminals),std::move(r.is_clock_net),std::move(r.rr_blk_source),std::move(r.rr_node_route_inf),std::move(r.net_terminal_groups),std::move(r.net_terminal_group_num),std::move(r.non_configurable_bitset),std::move(r.net_status),std::move(r.route_bb),std::move(r.clb_opins_used_locally),std::move(r.routing_id),std::move(r.is_flat));
  bool committed=false;std::string error;
  try{
   if(!real_read(candidate,saved_opts,true,false))throw std::runtime_error("candidate capacity infeasible");
   check_route(n,saved_opts.route_type,saved_opts.check_route,false);
   if(std::getenv("ROUTECAST_TX_FORCE_ROLLBACK"))throw std::runtime_error("forced post-validation rejection");
   committed=true;
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
  std::ofstream status(std::string(txprefix)+".json");status<<"{\"committed\":"<<(committed?"true":"false")<<",\"error\":"<<std::quoted(error)<<"}\n";
  if(!status)throw std::runtime_error("transaction status write failed");
 }
 real_sync(n,d,a,c,p,verbose);
 if(prefix&&*prefix)capture((std::string(prefix)+".after.jsonl").c_str());
}
