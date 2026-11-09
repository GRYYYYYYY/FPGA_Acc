#pragma once
#include "route_net.h"
#include "router_stats.h"
void routecast_trace_begin(const Netlist<>&);
void routecast_trace_decision_enter();
void routecast_trace_decision(ParentNetId,const char*,RRNodeId=RRNodeId::INVALID());
void routecast_trace_setup(int,ParentNetId,bool,bool);
void routecast_trace_iter_begin(int,const Netlist<>&);
void routecast_trace_routed(const Netlist<>&);
void routecast_trace_iter_end(int,const Netlist<>&,const RouterStats&);
void routecast_trace_finish(const Netlist<>&,bool);
