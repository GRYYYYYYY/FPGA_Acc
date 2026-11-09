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
extern bool routecast_candidate_synced;
extern "C" void wrapped_sync(const Nets& nets,const DeviceContext& device,AtomContext& atom,ClusteringContext& clustering,const PlacementContext& placement,const bool& verbose){
 if(routecast_candidate_synced){routecast_candidate_synced=false;VTR_LOG("ROUTECAST accepted candidate already synchronized; consume outer sync stage\n");return;}
 real_sync(nets,device,atom,clustering,placement,verbose);
}
