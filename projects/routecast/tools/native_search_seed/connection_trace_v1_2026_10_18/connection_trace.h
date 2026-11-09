#pragma once
void routecast_connection_trace_begin(const Netlist<>&);
void routecast_connection_iter_begin(int);
void routecast_connection_attempt(ParentNetId,int);
void routecast_connection_success(ParentNetId,int);
void routecast_connection_failure(ParentNetId,int);
void routecast_connection_iter_end(int,const RouterStats&);
void routecast_connection_trace_finish(bool);
