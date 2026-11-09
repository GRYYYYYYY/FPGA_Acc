#include "vpr_api.h"
#include "route_common.h"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
int main(int argc,char** argv){
 try{
  if(argc<4)throw std::runtime_error("output arch circuit required");std::vector<const char*> args{argv[0]};for(int i=2;i<argc;++i)args.push_back(argv[i]);t_options opts;t_vpr_setup setup;t_arch arch;vpr_init(int(args.size()),args.data(),&opts,&setup,&arch);vpr_load_packing(setup,arch);vpr_create_device(setup,arch,false);vpr_load_placement(setup,arch);
  if(setup.RouterOpts.fixed_channel_width!=128||setup.PlacerOpts.place_chan_width!=128)throw std::runtime_error("fixed width contract");
  const Netlist<>& netlist=g_vpr_ctx.clustering().clb_nlist;
  init_route_structs(netlist,setup.RouterOpts.bb_factor,false,false); // Terminals/bounds only; no search, commits or routing iterations.
  const auto& routing=g_vpr_ctx.routing();for(const auto& tree:routing.route_trees)if(tree)throw std::runtime_error("unexpected route tree");const auto& rr=g_vpr_ctx.device().rr_graph;std::size_t edges=0;for(auto n:rr.nodes())edges+=rr.num_edges(n);std::ofstream out(argv[1]);if(!out)throw std::runtime_error("output");out<<"H "<<rr.num_nodes()<<' '<<edges<<' '<<netlist.nets().size()<<'\n';
  for(auto net:netlist.nets()){const auto& terms=routing.net_rr_terminals[net];out<<"N "<<std::size_t(net)<<' '<<std::quoted(netlist.net_name(net))<<' '<<netlist.net_is_ignored(net)<<' '<<netlist.net_is_global(net)<<' '<<routing.is_clock_net[net]<<' '<<terms.size();for(auto n:terms)out<<' '<<std::size_t(n);out<<'\n';}
  if(!out)throw std::runtime_error("export failed");std::cout<<"PREROUTE_CONTEXT_EXPORTED_NO_ROUTE_TREES "<<rr.num_nodes()<<' '<<edges<<'\n';
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}return 0;
}
