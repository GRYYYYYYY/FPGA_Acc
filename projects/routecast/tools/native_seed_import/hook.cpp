#include "globals.h"
#include "route_common.h"
#include "read_route.h"
#include <cstdlib>
#include <cstdio>
#include <stdexcept>
extern "C" void original_init(const Netlist<>&,int,bool,bool) asm("__real__Z18init_route_structsRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEEibb");
extern "C" void seeded_init(const Netlist<>&,int,bool,bool) asm("__wrap__Z18init_route_structsRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEEibb");
extern "C" void seeded_init(const Netlist<>& nets,int bb,bool choke,bool flat){
 original_init(nets,bb,choke,flat);
 static bool entered=false;
 const char* seed=std::getenv("ROUTECAST_NATIVE_SEED");
 if(!seed||!*seed||entered)return;
 if(flat)throw std::runtime_error("seed prototype rejects flat routing");
 entered=true;
 t_router_opts opts{};opts.bb_factor=bb;opts.has_choke_point=choke;opts.flat_routing=false;opts.initial_pres_fac=0.5f;opts.acc_fac=1.0f;
 bool feasible=read_route(seed,opts,true,false);
 entered=false;
 std::fprintf(stderr,"ROUTECAST seed imported feasible=%d; explicit import pres_fac=0.5 acc_fac=1\n",int(feasible));
}
