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

#include <cstdint>
#include <limits>
#include <memory>
#include <sstream>
struct SyncTicket {
 const Nets* nets;
 const DeviceContext* device;
 const AtomContext* atom;
 const ClusteringContext* clustering;
 const PlacementContext* placement;
 uint64_t epoch;
 std::string state;
};
static thread_local std::unique_ptr<SyncTicket> ticket;
static thread_local uint64_t sync_epoch=0;
static std::string state_of(const Nets& nets,const PlacementContext& placement) {
 FILE* f=std::tmpfile();
 if(!f)throw std::runtime_error("sync ticket trace allocation failed");
 std::unique_ptr<FILE,decltype(&std::fclose)> guard(f,&std::fclose);
 print_route(nets,f,g_vpr_ctx.routing().is_flat);
 if(std::fflush(f)!=0 || std::fseek(f,0,SEEK_SET)!=0)throw std::runtime_error("sync ticket trace seek failed");
 std::string result;char buf[4096];size_t count;
 while((count=std::fread(buf,1,sizeof(buf),f)))result.append(buf,count);
 if(std::ferror(f))throw std::runtime_error("sync ticket trace read failed");
 std::ostringstream locs;locs<<"\nNETLIST "<<nets.netlist_id()<<"\nPLACEMENT "<<placement.placement_id<<"\n";
 for(auto block:g_vpr_ctx.clustering().clb_nlist.blocks()) {
  const auto& l=placement.blk_loc_registry().block_locs()[block].loc;
  locs<<size_t(block)<<':'<<l.x<<','<<l.y<<','<<l.sub_tile<<','<<l.layer<<'\n';
 }
 return result+locs.str();
}
void routecast_arm_sync_ticket(const Nets& nets,const DeviceContext& device,const AtomContext& atom,const ClusteringContext& clustering,const PlacementContext& placement) {
 if(ticket)throw std::runtime_error("unconsumed candidate sync ticket");
 if(sync_epoch==std::numeric_limits<uint64_t>::max())throw std::runtime_error("candidate sync epoch exhausted");
 auto pending=std::make_unique<SyncTicket>(SyncTicket{&nets,&device,&atom,&clustering,&placement,sync_epoch+1,state_of(nets,placement)});
 ++sync_epoch;ticket=std::move(pending);
 VTR_LOG("ROUTECAST armed context-bound candidate sync ticket epoch=%llu\n",(unsigned long long)sync_epoch);
}
extern "C" void wrapped_sync(const Nets& nets,const DeviceContext& device,AtomContext& atom,ClusteringContext& clustering,const PlacementContext& placement,const bool& verbose){
 if(ticket){
  if(ticket->nets!=&nets || ticket->device!=&device || ticket->atom!=&atom || ticket->clustering!=&clustering || ticket->placement!=&placement || ticket->epoch!=sync_epoch || ticket->state!=state_of(nets,placement))throw std::runtime_error("candidate sync ticket owner/state mismatch");
  VTR_LOG("ROUTECAST consume context-bound candidate sync ticket epoch=%llu\n",(unsigned long long)ticket->epoch);
  ticket.reset();return;
 }
 real_sync(nets,device,atom,clustering,placement,verbose);
}
