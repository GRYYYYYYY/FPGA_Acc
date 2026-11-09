#include "routecast_owner_trace.h"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#include <thread>
#include <vector>
namespace {
FILE* rc_trace_file=nullptr;
const Netlist<>* rc_trace_netlist=nullptr;
std::thread::id rc_trace_thread;
size_t rc_trace_event=0,rc_trace_q=0,rc_trace_last_q=0;
int rc_trace_iter=0;
bool rc_trace_pending=false;
ParentNetId rc_trace_net=ParentNetId::INVALID(),rc_trace_qnet=ParentNetId::INVALID();
void rc_trace_check() {
    if(std::this_thread::get_id()!=rc_trace_thread)throw std::runtime_error("owner trace requires same serial routing thread");
    if(std::ferror(rc_trace_file))throw std::runtime_error("owner trace write failed");
}
std::vector<size_t> rc_trace_nodes(ParentNetId net) {
    std::vector<size_t> nodes;
    const auto& tree=g_vpr_ctx.routing().route_trees[net];
    if(tree)for(const auto& node:tree->all_nodes())nodes.push_back(size_t(node.inode));
    std::sort(nodes.begin(),nodes.end()); // Preserve repeated RR IDs as multiplicities.
    return nodes;
}
void rc_trace_tree(ParentNetId net) {
    const auto& tree=g_vpr_ctx.routing().route_trees[net];
    const auto nodes=rc_trace_nodes(net);
    std::fprintf(rc_trace_file,"T %zu %d %d %zu %zu",size_t(net),int(rc_trace_netlist->net_is_ignored(net)),int(bool(tree)),tree?tree->get_remaining_isinks().size():size_t(0),nodes.size());
    for(auto n:nodes)std::fprintf(rc_trace_file," %zu",n);
    std::fputc('\n',rc_trace_file);
}
void rc_trace_value(size_t n) {
    const auto id=RRNodeId(n);const auto& ctx=g_vpr_ctx.routing();const auto& graph=g_vpr_ctx.device().rr_graph;
    std::fprintf(rc_trace_file,"V %zu %d %d\n",n,ctx.rr_node_route_inf[id].occ(),int(graph.node_capacity(id)));
}
void rc_trace_flush_pending() {
    if(!rc_trace_pending)return;
    std::fprintf(rc_trace_file,"E %zu %d %zu\n",rc_trace_event,rc_trace_iter,size_t(rc_trace_net));
    rc_trace_tree(rc_trace_net);std::fprintf(rc_trace_file,"EE\n");rc_trace_pending=false;
}
void rc_trace_checkpoint(const char* tag,const Netlist<>& nets) {
    rc_trace_flush_pending();
    std::fprintf(rc_trace_file,"CP %s %d\n",tag,rc_trace_iter);
    for(auto net:nets.nets())rc_trace_tree(net);
    const auto& ctx=g_vpr_ctx.routing();const auto& graph=g_vpr_ctx.device().rr_graph;
    for(size_t n=0;n<graph.num_nodes();++n)if(ctx.rr_node_route_inf[RRNodeId(n)].occ()>graph.node_capacity(RRNodeId(n)))rc_trace_value(n);
    std::fprintf(rc_trace_file,"CE\n");
    if(std::fflush(rc_trace_file)!=0)throw std::runtime_error("owner trace flush failed");
    rc_trace_check();
}
}
void routecast_trace_begin(const Netlist<>& nets) {
    const char* path=std::getenv("ROUTECAST_NATIVE_OWNER_TRACE");if(!path || !*path)return;
    if(rc_trace_file)throw std::runtime_error("owner trace rejects reentrant routing");
    rc_trace_file=std::fopen(path,"wx");if(!rc_trace_file)throw std::runtime_error("owner trace requires new exclusive output file");
    std::setvbuf(rc_trace_file,nullptr,_IOFBF,1<<20);rc_trace_thread=std::this_thread::get_id();rc_trace_netlist=&nets;
    rc_trace_event=rc_trace_q=rc_trace_last_q=0;rc_trace_iter=0;rc_trace_pending=false;rc_trace_qnet=ParentNetId::INVALID();
    std::fprintf(rc_trace_file,"TRACE 1\n");rc_trace_checkpoint("initial",nets);
}
void routecast_trace_decision_enter() {
    if(!rc_trace_file)return;rc_trace_check();rc_trace_flush_pending();
}
void routecast_trace_decision(ParentNetId net,const char* reason,RRNodeId node) {
    if(!rc_trace_file)return;rc_trace_check();rc_trace_last_q=++rc_trace_q;rc_trace_qnet=net;
    long long n=-1;int occ=-1,cap=-1;
    if(node!=RRNodeId::INVALID()){n=static_cast<long long>(size_t(node));occ=g_vpr_ctx.routing().rr_node_route_inf[node].occ();cap=g_vpr_ctx.device().rr_graph.node_capacity(node);}
    std::fprintf(rc_trace_file,"Q %zu %d %zu %s %lld %d %d\n",rc_trace_q,rc_trace_iter,size_t(net),reason,n,occ,cap);
}
void routecast_trace_setup(int itry,ParentNetId net,bool preserve,bool hold) {
    if(!rc_trace_file)return;rc_trace_check();rc_trace_flush_pending();
    if(itry!=rc_trace_iter)throw std::runtime_error("owner trace iteration mismatch");
    rc_trace_net=net;++rc_trace_event;rc_trace_pending=true;
    std::fprintf(rc_trace_file,"B %zu %d %zu %d %d %zu\n",rc_trace_event,itry,size_t(net),int(preserve),int(hold),net==rc_trace_qnet?rc_trace_last_q:size_t(0));
    rc_trace_tree(net);auto nodes=rc_trace_nodes(net);nodes.erase(std::unique(nodes.begin(),nodes.end()),nodes.end());
    for(auto n:nodes)if(g_vpr_ctx.routing().rr_node_route_inf[RRNodeId(n)].occ()>g_vpr_ctx.device().rr_graph.node_capacity(RRNodeId(n)))rc_trace_value(n);
    std::fprintf(rc_trace_file,"BE\n");rc_trace_check();
}
void routecast_trace_iter_begin(int itry,const Netlist<>& nets) {
    if(!rc_trace_file)return;rc_trace_check();rc_trace_flush_pending();rc_trace_iter=itry;rc_trace_checkpoint("iteration_begin",nets);
}
void routecast_trace_routed(const Netlist<>& nets) {
    if(!rc_trace_file)return;rc_trace_check();rc_trace_checkpoint("routed_before_local_opins",nets);
}
void routecast_trace_iter_end(int itry,const Netlist<>& nets,const RouterStats& stats) {
    if(!rc_trace_file)return;rc_trace_check();if(itry!=rc_trace_iter)throw std::runtime_error("owner trace stats iteration mismatch");
    std::fprintf(rc_trace_file,"S %d %zu %zu %zu %zu\n",itry,stats.nets_routed,stats.connections_routed,stats.heap_pushes,stats.heap_pops);
    rc_trace_checkpoint("iteration_end_after_local_opins",nets);
}
void routecast_trace_finish(const Netlist<>& nets,bool success) {
    if(!rc_trace_file)return;rc_trace_check();rc_trace_checkpoint("final_after_best_restore",nets);
    std::fprintf(rc_trace_file,"END %d %zu %zu\n",int(success),rc_trace_q,rc_trace_event);
    FILE* closed=rc_trace_file;rc_trace_file=nullptr;rc_trace_netlist=nullptr;
    if(std::fclose(closed)!=0)throw std::runtime_error("owner trace close failed");
}
