"""Read-only branch observations in owned connection router and ledger observer."""
import json,subprocess,shutil
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'build/prince_competitive_frontier_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);old=R/'build/prince_ownership_ledger_v2_2026-10-20';prior=R/'build/prince_connection_query_v1_2026-10-20';p=json.loads((old/'protocol.json').read_text());cs=prior/'connection_router.cpp';s=cs.read_text();decl='extern "C" void routecast_frontier_event(int,RRNodeId,RRNodeId,RRNodeId,float,float,float,float,bool);\n';s=decl+s if False else s.replace('extern "C" void routecast_connection_end();','extern "C" void routecast_connection_end();\n'+decl)
 needle='''        (rcv_path_manager.is_enabled() && best_total_cost > new_total_cost)) {''';assert s.count(needle)==1;s=s.replace(needle,needle+'\n        routecast_frontier_event(1,from_node,to_node,target_node,best_back_cost,new_back_cost,best_total_cost,new_total_cost,rcv_path_manager.is_enabled());')
 needle='''    } else {
        VTR_LOGV_DEBUG(router_debug_, "      Didn't expand to %d (%s)''';assert s.count(needle)==1;s=s.replace(needle,'''    } else {
        routecast_frontier_event(2,from_node,to_node,target_node,best_back_cost,new_back_cost,best_total_cost,new_total_cost,rcv_path_manager.is_enabled());
        VTR_LOGV_DEBUG(router_debug_, "      Didn't expand to %d (%s)''')
 needle='''    if (best_total_cost == new_total_cost) {''';assert s.count(needle)==1;s=s.replace(needle,needle+'\n        routecast_frontier_event(3,from_node,from_node,target_node,rr_node_route_inf_[from_node].backward_path_cost,0.f,best_total_cost,new_total_cost,rcv_path_manager.is_enabled());')
 needle='''    } else {
        // Post-heap prune''';assert s.count(needle)==1;s=s.replace(needle,'''    } else {
        routecast_frontier_event(4,from_node,from_node,target_node,rr_node_route_inf_[from_node].backward_path_cost,0.f,best_total_cost,new_total_cost,rcv_path_manager.is_enabled());
        // Post-heap prune''')
 cp=D/'connection_router.cpp';cp.write_text(s);s=(old/'observer.cpp').read_text();s=s.replace('static int phase_iteration=0;', 'static bool frontier_closed=false;\nstatic void frontier_boundary(int);\nstatic void frontier_connection_end();\nstatic int phase_iteration=0;',1);s=s.replace(' flush_queries(i);',' flush_queries(i);frontier_boundary(i);',1);needle=' if(ready){';assert s.count(needle)==1;s=s.replace(needle,needle+'\n  frontier_closed=true;',1);needle='extern "C" void routecast_connection_end(){if(!connection_active)throw std::runtime_error("connection close mismatch");connection_active=false;connection_owned.clear();}';assert s.count(needle)==1;s=s.replace(needle,needle.replace('connection_active=false;','frontier_connection_end();connection_active=false;'))
 s+='''
static uint64_t frontier_sequence=0,frontier_counts[4]={0,0,0,0};
static bool frontier_enabled(){static bool enabled=std::getenv("ROUTECAST_FRONTIER_FILE")!=nullptr;return enabled;}
static std::ofstream& frontier_stream(){static std::ofstream f(std::getenv("ROUTECAST_FRONTIER_FILE"),std::ios::binary);static bool header=false;if(!f)throw std::runtime_error("frontier open");if(!header){f.write("RCFRNT01",8);header=true;}return f;}
extern "C" void routecast_frontier_event(int tag,RRNodeId from,RRNodeId node,RRNodeId target,float best_back,float new_back,float best_total,float new_total,bool rcv){
 if(!frontier_enabled()||frontier_closed||!channel(size_t(node)))return;
 if(!connection_active||!query_scope||query_net<0||tag<1||tag>4)throw std::runtime_error("frontier scope");
 const auto& d=g_vpr_ctx.device();
 std::array<uint64_t,18> row{{uint64_t(tag),uint64_t(phase_iteration+1),uint64_t(query_net),connection_id,connection_pin,connection_sink,size_t(from),size_t(node),size_t(target),uint64_t(d.rr_graph.node_type(node)),ledger_epoch,qbits(best_back),qbits(new_back),qbits(best_total),qbits(new_total),uint64_t(rcv),uint64_t(connection_owned.count(size_t(node))),++frontier_sequence}};
 frontier_stream().write(reinterpret_cast<const char*>(row.data()),sizeof(row));++frontier_counts[tag-1];
}
static void frontier_connection_end(){
 if(!frontier_enabled()||frontier_closed)return;
 static std::ofstream f(std::string(std::getenv("ROUTECAST_FRONTIER_FILE"))+".connection_ends.bin",std::ios::binary);std::array<uint64_t,4> row{{uint64_t(phase_iteration+1),uint64_t(query_net),connection_id,ledger_epoch}};f.write(reinterpret_cast<const char*>(row.data()),sizeof(row));if(!f)throw std::runtime_error("frontier connection end");
}
static void frontier_boundary(int iteration){
 if(!frontier_enabled())return;
 if(frontier_sequence){frontier_stream().flush();if(!frontier_stream())throw std::runtime_error("frontier event write");}
 std::ofstream f(std::string(std::getenv("ROUTECAST_FRONTIER_FILE"))+".phases.tsv",std::ios::app);f<<iteration;for(auto n:frontier_counts)f<<'\\t'<<n;f<<'\\t'<<frontier_sequence<<'\\t'<<frontier_closed<<'\\n';if(!f)throw std::runtime_error("frontier phase write");for(auto& n:frontier_counts)n=0;
}
'''
 op=D/'observer.cpp';op.write_text(s);cc=json.loads((prior/'protocol.json').read_text())['connection_compile'];cc[cc.index('-c')+1]=str(cp);cc[cc.index('-o')+1]=str(D/'connection_router.cpp.o');oc=p['compile'].copy();oc[oc.index('-c')+1]=str(op);oc[oc.index('-o')+1]=str(D/'observer.o');link=p['link'].copy();link=[str(D/'observer.o') if x==str(old/'observer.o') else x for x in link];link[link.index('-o')+1]=str(D/'vpr');archive=next(Path(x) for x in link if x.endswith('/libvpr.a'));owned=D/'libvpr.a';shutil.copyfile(archive,owned);link=[str(owned) if x==str(archive) else x for x in link];design=R/'experiments/prince_causal_query_frontier_v1_2026-10-20/native_competitive_frontier_observation_design_v1.json';bindings={str(x):sha(x) for x in [Path(__file__),old/'protocol.json',old/'receipt.json',old/'observer.cpp',prior/'protocol.json',cs,cp,op,archive,design]};schema=dict(magic='RCFRNT01',record='18 little-endian uint64 words',fields=['tag','iteration','native_NET','connection_id','pin','sink','from_node','node','target','kind','entry_ledger_epoch','best_back_bits','new_back_bits','best_total_bits','new_total_bits','RCV_enabled','entry_owned','sequence'],tags={'1':'preheap accepted','2':'preheap rejected','3':'valid pop expansion','4':'stale pop'},pop_new_back='zero sentinel,not observed popped backward cost',connection_ends='4 uint64 words iteration,NET,connection_id,ledger_epoch;no header',cutoff='Record only through first actual ready boundary;all subsequent events disabled. Width96 no ready retained through terminal.',commit='Event ledger and exact connection close records support branch-add attribution;valid pop alone not commit.')
 (D/'protocol.json').write_text(json.dumps(dict(connection_compile=cc,compile=oc,link=link,bindings=bindings,schema=schema,scope='Original native if conditions and floating expressions unchanged; hooks inside actual branches,raw float words only. Owned copied library replaces only connection_router.cpp.o; existing route restore object unchanged.'),indent=2)+'\n')
 for name,cmd in [('connection_compile',cc),('observer_compile',oc),('archive_replace',['ar','r',str(owned),str(D/'connection_router.cpp.o')]),('link',link)]:
  with (D/(name+'.log')).open('x') as f:code=subprocess.call(cmd,cwd=D,stdout=f,stderr=subprocess.STDOUT)
  print(name,code,flush=True)
  if code:raise SystemExit(code)
 assert all(sha(x)==h for x,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(D/'vpr'),bindings={str(x):sha(x) for x in [D/'protocol.json',owned,op,cp,D/'observer.o',D/'connection_router.cpp.o']}),indent=2)+'\n')
if __name__=='__main__':main()
