#include <string>
namespace {
FILE* rc_conn_file=nullptr;
size_t rc_conn_push_before=0,rc_conn_pop_before=0,rc_conn_iter_pushes=0,rc_conn_iter_pops=0,rc_conn_total_pushes=0,rc_conn_total_pops=0;
size_t rc_conn_serial=0,rc_conn_successes=0,rc_conn_failures=0,rc_conn_iter_successes=0;
bool rc_conn_pending=false;
ParentNetId rc_conn_net=ParentNetId::INVALID();
int rc_conn_pin=-1;
void rc_conn_result(const char* tag,ParentNetId net,int pin,const RouterStats& stats) {
    if(!rc_conn_pending || net!=rc_conn_net || pin!=rc_conn_pin)throw std::runtime_error("connection observer unmatched result");
    if(stats.heap_pushes<rc_conn_push_before || stats.heap_pops<rc_conn_pop_before)throw std::runtime_error("connection work counters decreased within attempt");
    const size_t pushes=stats.heap_pushes-rc_conn_push_before,pops=stats.heap_pops-rc_conn_pop_before;
    rc_conn_iter_pushes+=pushes;rc_conn_iter_pops+=pops;rc_conn_total_pushes+=pushes;rc_conn_total_pops+=pops;
    std::fprintf(rc_conn_file,"%s %zu %d %zu %d %zu %zu\n",tag,rc_conn_serial,rc_trace_iter,size_t(net),pin,stats.heap_pushes,stats.heap_pops);
    rc_conn_pending=false;
}
}
void routecast_connection_trace_begin(const Netlist<>& nets) {
    const char* path=std::getenv("ROUTECAST_NATIVE_CONNECTION_TRACE");if(!path || !*path)return;
    if(rc_conn_file)throw std::runtime_error("connection observer reentrant");
    rc_conn_file=std::fopen(path,"wx");if(!rc_conn_file)throw std::runtime_error("connection observer exclusive file required");
    std::setvbuf(rc_conn_file,nullptr,_IOFBF,1<<20);
    std::fprintf(rc_conn_file,"CONNECTION_TRACE 2\n");
    const auto& ctx=g_vpr_ctx.routing();
    for(auto net:nets.nets()) {
        const auto count=nets.net_pins(net).size();
        std::fprintf(rc_conn_file,"N %zu %d %zu ",size_t(net),int(nets.net_is_ignored(net)),count);
        for(unsigned char c:nets.net_name(net))std::fprintf(rc_conn_file,"%02x",unsigned(c));
        std::fputc('\n',rc_conn_file);
        const auto& terms=ctx.net_rr_terminals[net];
        if(!nets.net_is_ignored(net) && terms.size()!=count)throw std::runtime_error("connection observer terminal dimension");
        const auto& tree=ctx.route_trees[net];
        for(size_t pin=0;pin<terms.size();++pin) {
            const bool reached=pin>0 && tree && tree->get_is_isink_reached().get(pin);
            std::fprintf(rc_conn_file,"P %zu %zu %zu %d\n",size_t(net),pin,size_t(terms[pin]),int(reached));
        }
    }
    if(std::fflush(rc_conn_file)!=0)throw std::runtime_error("connection observer initial flush");
}
void routecast_connection_iter_begin(int iteration) {
    if(!rc_conn_file)return;rc_trace_check();
    if(rc_conn_pending)throw std::runtime_error("connection observer pending at iteration begin");
    rc_conn_iter_successes=0;rc_conn_iter_pushes=rc_conn_iter_pops=0;std::fprintf(rc_conn_file,"I %d\n",iteration);
}
void routecast_connection_attempt(ParentNetId net,int pin,const RouterStats& stats) {
    if(!rc_conn_file)return;rc_trace_check();
    if(rc_conn_pending || !rc_trace_pending || net!=rc_trace_net || pin<=0)throw std::runtime_error("connection observer unsupported attempt context");
    const auto& terms=g_vpr_ctx.routing().net_rr_terminals[net];
    if(size_t(pin)>=terms.size())throw std::runtime_error("connection observer pin index");
    rc_conn_pending=true;rc_conn_net=net;rc_conn_pin=pin;++rc_conn_serial;rc_conn_push_before=stats.heap_pushes;rc_conn_pop_before=stats.heap_pops;
    std::fprintf(rc_conn_file,"A %zu %d %zu %d %zu %zu %zu %zu\n",rc_conn_serial,rc_trace_iter,size_t(net),pin,size_t(terms[0]),size_t(terms[pin]),stats.heap_pushes,stats.heap_pops);
}
void routecast_connection_success(ParentNetId net,int pin,const RouterStats& stats) {
    if(!rc_conn_file)return;rc_trace_check();rc_conn_result("C",net,pin,stats);++rc_conn_successes;++rc_conn_iter_successes;
}
void routecast_connection_failure(ParentNetId net,int pin,const RouterStats& stats) {
    if(!rc_conn_file)return;rc_trace_check();rc_conn_result("F",net,pin,stats);++rc_conn_failures;
}
void routecast_connection_iter_end(int iteration,const RouterStats& stats) {
    if(!rc_conn_file)return;rc_trace_check();
    if(rc_conn_pending || rc_conn_iter_successes!=stats.connections_routed)throw std::runtime_error("connection observer native counter mismatch");
    if(rc_conn_iter_pushes>stats.heap_pushes || rc_conn_iter_pops>stats.heap_pops)throw std::runtime_error("connection work attribution exceeds native totals");
    std::fprintf(rc_conn_file,"S %d %zu %zu %zu %zu %zu %zu\n",iteration,rc_conn_iter_successes,stats.connections_routed,rc_conn_iter_pushes,rc_conn_iter_pops,stats.heap_pushes,stats.heap_pops);
    if(std::fflush(rc_conn_file)!=0)throw std::runtime_error("connection observer stats flush");
}
void routecast_connection_trace_finish(bool success) {
    if(!rc_conn_file)return;rc_trace_check();
    if(rc_conn_pending || rc_conn_serial!=rc_conn_successes+rc_conn_failures)throw std::runtime_error("connection observer incomplete attempts");
    std::fprintf(rc_conn_file,"END %d %zu %zu %zu %zu %zu\n",int(success),rc_conn_serial,rc_conn_successes,rc_conn_failures,rc_conn_total_pushes,rc_conn_total_pops);
    FILE* old=rc_conn_file;rc_conn_file=nullptr;if(std::fclose(old)!=0)throw std::runtime_error("connection observer close failed");
}
