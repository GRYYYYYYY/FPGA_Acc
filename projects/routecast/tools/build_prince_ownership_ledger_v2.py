"""Ledger v2 covers native best-routing restoration using explicit NET IDs."""
import json,subprocess,shutil
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'build/prince_ownership_ledger_v2_2026-10-20'
def main():
 D.mkdir(exist_ok=False);old=R/'build/prince_ownership_ledger_v1_2026-10-20';p=json.loads((old/'protocol.json').read_text());s=(old/'observer.cpp').read_text();s=s.replace('static void consume_boundary(int);','static void consume_boundary(int);\nstatic void ledger_final();');s=s.replace('static uint64_t ledger_epoch=0;','static uint64_t ledger_epoch=0;\nstatic bool ledger_restoring=false;');s=s.replace('ledger_word(1);ledger_word(ledger_epoch);','ledger_word(ledger_restoring?4:1);ledger_word(ledger_epoch);')
 lines=s.splitlines()
 for idx,line in enumerate(lines):
  if 'active_config=digest;return __real__Z5route' in line:lines[idx]=line.replace('active_config=digest;return ','active_config=digest;bool result=')+'ledger_final();return result;'
 s='\n'.join(lines)+'\n'
 s+='''
extern "C" void routecast_restore_tree(const RouteTreeNode& root,int delta,size_t net){
 bool old_scope=query_scope;int old_net=query_net;query_scope=true;query_net=int(net);ledger_restoring=true;
 __wrap__Z38pathfinder_update_cost_from_route_treeRK13RouteTreeNodei(root,delta);
 ledger_restoring=false;query_scope=old_scope;query_net=old_net;
}
static void ledger_final(){
 if(!std::getenv("ROUTECAST_QUERY_FILE"))return;
 const auto& routing=g_vpr_ctx.routing();std::map<size_t,std::set<size_t>> actual;
 for(auto net:routing.route_trees.keys())if(routing.route_trees[net]){auto& group=actual[size_t(net)];const auto& root=routing.route_trees[net]->root();if(channel(size_t(root.inode)))group.insert(size_t(root.inode));for(const auto& node:root.all_nodes())if(channel(size_t(node.inode)))group.insert(size_t(node.inode));}
 for(const auto& item:actual)if(item.second!=ledger_owners[item.first])throw std::runtime_error("terminal tree/ledger mismatch");
 for(const auto& item:ledger_owners)if(item.second!=actual[item.first])throw std::runtime_error("terminal absent tree/ledger mismatch");
 for(auto node:g_vpr_ctx.device().rr_graph.nodes())if(channel(size_t(node))&&ledger_counts[size_t(node)]!=routing.rr_node_route_inf[node].occ())throw std::runtime_error("terminal occupancy mismatch");
 ledger_word(5);ledger_word(ledger_epoch);ledger_word(actual.size());for(const auto& item:actual){ledger_word(item.first);ledger_word(item.second.size());for(auto node:item.second)ledger_word(node);}ledger_stream().flush();if(!ledger_stream())throw std::runtime_error("terminal ledger write");
}
'''
 op=D/'observer.cpp';op.write_text(s);compile=p['compile'].copy();compile[compile.index('-c')+1]=str(op);compile[compile.index('-o')+1]=str(D/'observer.o');vendor=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';native=vendor/'vpr/src/route/route.cpp';rs=native.read_text();rs=rs.replace('bool route(const Netlist<>& net_list,','extern "C" void routecast_restore_tree(const RouteTreeNode&,int,size_t);\n\nbool route(const Netlist<>& net_list,',1)
 for expr in ['route_ctx.route_trees[net_id]->root(), -1','best_routing[net_id]->root(), 1']:
  needle='pathfinder_update_cost_from_route_tree('+expr+');';assert rs.count(needle)==1;rs=rs.replace(needle,'routecast_restore_tree('+expr+', size_t(net_id));')
 rp=D/'route.cpp';rp.write_text(rs);cc=json.loads((R/'build/prince_connection_query_v1_2026-10-20/protocol.json').read_text())['connection_compile'];cc[cc.index('-c')+1]=str(rp);cc[cc.index('-o')+1]=str(D/'route.cpp.o');link=p['link'].copy();link=[str(D/'observer.o') if x==str(old/'observer.o') else x for x in link];link[link.index('-o')+1]=str(D/'vpr');archive=next(Path(x) for x in link if x.endswith('/libvpr.a'));owned=D/'libvpr.a';shutil.copyfile(archive,owned);link=[str(owned) if x==str(archive) else x for x in link];bindings={str(q):sha(q) for q in [Path(__file__),old/'protocol.json',old/'receipt.json',old/'observer.cpp',archive,native,rp,op]};(D/'protocol.json').write_text(json.dumps(dict(compile=compile,route_compile=cc,link=link,bindings=bindings,scope='Owned source copies: connection entry RAII plus explicit NET argument on two best-routing restore updates. Native order/arguments unchanged. v1 terminal restore context failure preserved. No predictive cost changes.'),indent=2)+'\n')
 for name,cmd in [('route_compile',cc),('observer_compile',compile),('archive_replace',['ar','r',str(owned),str(D/'route.cpp.o')]),('link',link)]:
  with (D/(name+'.log')).open('x') as f:code=subprocess.call(cmd,cwd=D,stdout=f,stderr=subprocess.STDOUT)
  print(name,code,flush=True)
  if code:raise SystemExit(code)
 assert all(sha(q)==h for q,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(D/'vpr'),bindings={str(q):sha(q) for q in [D/'protocol.json',owned,op,rp,D/'observer.o',D/'route.cpp.o']}),indent=2)+'\n')
if __name__=='__main__':main()
