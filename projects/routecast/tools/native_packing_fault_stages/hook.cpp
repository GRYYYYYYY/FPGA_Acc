#include "globals.h"
#include "vpr_context.h"
#include "read_route.h"
#include <cstdlib>
#include <cstdio>
#include <string>
#include <stdexcept>
#include <sstream>
#include <fstream>
#include <vector>
#include <type_traits>
#include "vpr_error.h"
using Nets = Netlist<>;
void print_route(const Nets&,FILE*,bool);
extern "C" void real_sync(const Nets&,const DeviceContext&,AtomContext&,ClusteringContext&,const PlacementContext&,const bool&) asm("__real__Z24sync_netlists_to_routingRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEERK13DeviceContextR11AtomContextR17ClusteringContextRK16PlacementContextRKb");
extern "C" void wrapped_sync(const Nets&,const DeviceContext&,AtomContext&,ClusteringContext&,const PlacementContext&,const bool&) asm("__wrap__Z24sync_netlists_to_routingRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEERK13DeviceContextR11AtomContextR17ClusteringContextRK16PlacementContextRKb");

static void collect(t_pb* pb,std::vector<std::pair<t_pb*,t_pb>>& saved){
 saved.emplace_back(pb,*pb);
 if(pb->child_pbs)for(int t=0;t<pb->get_num_child_types();++t)for(int c=0;c<pb->get_num_children_of_type(t);++c)collect(&pb->child_pbs[t][c],saved);
}
static std::string state(AtomContext& atom,ClusteringContext& cluster){
 std::ostringstream f;
 for(auto block:cluster.clb_nlist.blocks()) {
  f<<"block "<<size_t(block)<<"\n";
  for(const auto& kv:cluster.clb_nlist.block_pb(block)->pb_route){
   const auto& r=kv.second;f<<kv.first<<" "<<size_t(r.atom_net_id)<<" "<<r.driver_pb_pin_id<<" "<<r.pb_graph_pin;
   for(auto sink:r.sink_pb_pin_ids)f<<" "<<sink;f<<"\n";
  }
 }
 for(auto pin:atom.nlist.pins()) {
  auto gp=atom.lookup.atom_pin_pb_graph_pin(pin);f<<"pin "<<size_t(pin)<<" "<<gp;
  if(gp)f<<" "<<atom.lookup.atom_pb(atom.nlist.pin_block(pin))->atom_pin_bit_index(gp);
  f<<"\n";
 }
 for(const auto& b:cluster.post_routing_clb_pin_nets)for(const auto& p:b.second)f<<"post "<<size_t(b.first)<<" "<<p.first<<" "<<size_t(p.second)<<"\n";
 for(const auto& b:cluster.pre_routing_net_pin_mapping)for(const auto& p:b.second)f<<"pre "<<size_t(b.first)<<" "<<p.first<<" "<<p.second<<"\n";
 return f.str();
}
template<class F> struct RestoreGuard { F restore; bool active=true; ~RestoreGuard() noexcept { if(active)restore(); } };
extern "C" void wrapped_sync(const Nets& nets,const DeviceContext& device,AtomContext& atom,ClusteringContext& clustering,const PlacementContext& placement,const bool& verbose){
 const char* dir=std::getenv("ROUTECAST_PACKING_ROLLBACK_DIR");
 if(!dir||!*dir){real_sync(nets,device,atom,clustering,placement,verbose);return;}
 std::vector<std::pair<t_pb*,t_pb>> saved;
 for(auto block:clustering.clb_nlist.blocks())collect(clustering.clb_nlist.block_pb(block),saved);
 auto lookup=atom.lookup;auto post=clustering.post_routing_clb_pin_nets;auto pre=clustering.pre_routing_net_pin_mapping;
 auto before=state(atom,clustering);
 auto restore=[&]() noexcept {
  static_assert(std::is_nothrow_swappable<t_pb>::value,"pb restore must not throw");
  static_assert(std::is_nothrow_swappable<AtomLookup>::value,"lookup restore must not throw");
  for(auto& entry:saved)std::swap(*entry.first,entry.second);
  std::swap(atom.lookup,lookup);clustering.post_routing_clb_pin_nets.swap(post);clustering.pre_routing_net_pin_mapping.swap(pre);
 };
 RestoreGuard<decltype(restore)> guard{restore};
 bool caught=false;
 try { real_sync(nets,device,atom,clustering,placement,verbose); }
 catch (...) {
  caught=true;
  std::ofstream(std::string(dir)+"/mutated.txt")<<state(atom,clustering);
  restore();guard.active=false;
 }
 if(!caught)throw std::runtime_error("packing fault was not reached");
 unsetenv("ROUTECAST_SYNC_FAULT_STAGE");
 auto restored=state(atom,clustering);if(before!=restored)throw std::runtime_error("packing rollback state mismatch");
 std::ofstream(std::string(dir)+"/before.txt")<<before;std::ofstream(std::string(dir)+"/restored.txt")<<restored;
 VTR_LOG("ROUTECAST restored packing hierarchy, pin rotations and atom lookup after sync failure\n");
 real_sync(nets,device,atom,clustering,placement,verbose);
}
