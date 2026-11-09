#include <string>
#include <cstdint>
#include <limits>
namespace {
FILE* rc_conn_file=nullptr;
FILE* rc_seed_file=nullptr;
FILE* rc_phase_file=nullptr;
bool rc_phase_active=false;
std::uint64_t rc_phase_ordinal=0,rc_phase_mode=0,rc_phase_records=0,rc_phase_seeds=0,rc_phase_begins=0,rc_phase_ends=0,rc_phase_outside=0;
std::uint64_t rc_seed_records=0,rc_seed_inside=0,rc_seed_outside=0;
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
    if(rc_phase_active)throw std::runtime_error("seed phase still open at connection result");
    rc_conn_pending=false;
}
}
void routecast_connection_trace_begin(const Netlist<>& nets) {
    const char* path=std::getenv("ROUTECAST_NATIVE_CONNECTION_TRACE");if(!path || !*path)return;
    if(rc_conn_file)throw std::runtime_error("connection observer reentrant");
    rc_conn_file=std::fopen(path,"wx");if(!rc_conn_file)throw std::runtime_error("connection observer exclusive file required");
    std::setvbuf(rc_conn_file,nullptr,_IOFBF,1<<20);
    std::fprintf(rc_conn_file,"CONNECTION_TRACE 2\n");
    const char* seedpath=std::getenv("ROUTECAST_NATIVE_SEED_CONTEXT_TRACE");
    if(seedpath && *seedpath) {
        const std::uint16_t endian=1;if(*reinterpret_cast<const unsigned char*>(&endian)!=1)throw std::runtime_error("seed context requires little endian");
        rc_seed_file=std::fopen(seedpath,"wbx");if(!rc_seed_file)throw std::runtime_error("seed context exclusive file required");
        std::setvbuf(rc_seed_file,nullptr,_IOFBF,1<<20);std::fputs("RC_SEED_PUSH_LE64 1\n",rc_seed_file);
        const char* phasepath=std::getenv("ROUTECAST_NATIVE_SEED_PHASE_TRACE");
        if(phasepath && *phasepath) {
            rc_phase_file=std::fopen(phasepath,"wbx");if(!rc_phase_file)throw std::runtime_error("seed phase exclusive file required");
            std::setvbuf(rc_phase_file,nullptr,_IOFBF,1<<20);std::fputs("RC_SEED_PHASE_LE64 1\n",rc_phase_file);
        }
    }
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
    if(rc_phase_active)throw std::runtime_error("phase pending at next attempt");rc_phase_ordinal=0;
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
    if(rc_seed_file) {
        const std::uint64_t end[4]={std::numeric_limits<std::uint64_t>::max(),rc_seed_records,rc_seed_inside,rc_seed_outside};
        if(std::fwrite(end,sizeof(end),1,rc_seed_file)!=1 || std::fclose(rc_seed_file)!=0)throw std::runtime_error("seed context footer/close failed");rc_seed_file=nullptr;
    }
    if(rc_phase_file) {
        if(rc_phase_active || rc_phase_begins!=rc_phase_ends)throw std::runtime_error("seed phase incomplete at END");
        const std::uint64_t footer[6]={std::numeric_limits<std::uint64_t>::max(),rc_phase_records,rc_phase_seeds,rc_phase_begins,rc_phase_ends,rc_phase_outside};
        if(std::fwrite(footer,sizeof(footer),1,rc_phase_file)!=1 || std::fclose(rc_phase_file)!=0)throw std::runtime_error("seed phase footer/close failed");rc_phase_file=nullptr;
    }
}

void routecast_connection_seed_push(std::size_t node,std::size_t target,std::size_t heap_pushes,std::size_t heap_pops) {
    if(!rc_seed_file)return;
    if(rc_conn_pending && size_t(g_vpr_ctx.routing().net_rr_terminals[rc_conn_net][rc_conn_pin])!=target)throw std::runtime_error("seed context target mismatch");
    const std::uint64_t row[4]={rc_conn_pending?rc_conn_serial:0,node,target,heap_pushes};
    if(std::fwrite(row,sizeof(row),1,rc_seed_file)!=1)throw std::runtime_error("seed context record failed");
    ++rc_seed_records;if(rc_conn_pending)++rc_seed_inside;else ++rc_seed_outside;
    if(rc_phase_file) {
        if(rc_conn_pending && !rc_phase_active)throw std::runtime_error("seed push outside active phase");
        const std::uint64_t event[6]={2,rc_conn_pending?rc_conn_serial:0,node,target,heap_pushes,heap_pops};
        if(std::fwrite(event,sizeof(event),1,rc_phase_file)!=1)throw std::runtime_error("seed phase push write failed");
        ++rc_phase_records;++rc_phase_seeds;if(!rc_conn_pending)++rc_phase_outside;
    }
}

void routecast_connection_seed_phase_begin(std::size_t mode,std::size_t pushes,std::size_t pops) {
    if(!rc_phase_file || !rc_conn_pending)return;
    if(rc_phase_active || mode>1)throw std::runtime_error("seed phase begin state");
    rc_phase_active=true;rc_phase_mode=mode;++rc_phase_ordinal;
    const std::uint64_t event[6]={1,rc_conn_serial,rc_phase_ordinal,mode,pushes,pops};
    if(std::fwrite(event,sizeof(event),1,rc_phase_file)!=1)throw std::runtime_error("seed phase begin write failed");++rc_phase_records;++rc_phase_begins;
}
void routecast_connection_seed_phase_end(std::size_t mode,std::size_t pushes,std::size_t pops) {
    if(!rc_phase_file || !rc_conn_pending)return;
    if(!rc_phase_active || mode!=rc_phase_mode)throw std::runtime_error("seed phase end state");
    const std::uint64_t event[6]={3,rc_conn_serial,rc_phase_ordinal,mode,pushes,pops};
    if(std::fwrite(event,sizeof(event),1,rc_phase_file)!=1)throw std::runtime_error("seed phase end write failed");++rc_phase_records;++rc_phase_ends;rc_phase_active=false;
}
