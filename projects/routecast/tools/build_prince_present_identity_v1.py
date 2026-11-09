"""Return capacity-one conditional present identity cost, with original-bit assertion."""
import json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'build/prince_present_identity_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);old=R/'build/prince_ownership_ledger_v2_2026-10-20';p=json.loads((old/'protocol.json').read_text());s=(old/'observer.cpp').read_text();s=s.replace('static void ledger_query(RRNodeId);','static void ledger_query(RRNodeId);\nstatic float conditional_identity(RRNodeId,float,float);\nstatic uint64_t identity_returns=0;')
 needle=' float value=__real__Z16get_rr_cong_costN3vtr8StrongIdI14rr_node_id_tagjLj4294967295EEEf(node,pres);';assert s.count(needle)==1;s=s.replace(needle,needle+'\n if(std::getenv("ROUTECAST_PRESENT_IDENTITY"))value=conditional_identity(node,pres,value);')
 s=s.replace("<<query_digest<<'\\n';", "<<query_digest<<'\\t'<<identity_returns<<'\\n';")
 s=s.replace('ledger_boundary(iteration);query_calls=', 'ledger_boundary(iteration);identity_returns=0;query_calls=')
 s+='''
static float conditional_identity(RRNodeId node,float pres,float original){
 if(!channel(size_t(node)))return original;
 const auto& d=g_vpr_ctx.device();const auto& rt=g_vpr_ctx.routing();
 if(d.rr_graph.node_capacity(node)!=1||rt.non_configurable_bitset.get(node))throw std::runtime_error("identity consumer unsupported CHANNEL capacity/group");
 if(!connection_active||query_net<0)throw std::runtime_error("identity consumer context missing");
 ledger_query(node);int owned=int(connection_owned.count(size_t(node)));int occupancy=rt.rr_node_route_inf[node].occ();if(occupancy<owned)throw std::runtime_error("identity negative other demand");
 float future_other=float(occupancy-owned);float marginal_excess=float(owned)+future_other;
 float replacement_present=(1.+pres*marginal_excess);
 auto index=d.rr_graph.node_cost_index(node);float replacement=d.rr_indexed_data[index].base_cost*rt.rr_node_route_inf[node].acc_cost*replacement_present;
 if(qbits(replacement)!=qbits(original))throw std::runtime_error("identity returned cost word differs");
 ++identity_returns;return replacement;
}
'''
 op=D/'observer.cpp';op.write_text(s);compile=p['compile'].copy();compile[compile.index('-c')+1]=str(op);compile[compile.index('-o')+1]=str(D/'observer.o');link=p['link'].copy();link=[str(D/'observer.o') if x==str(old/'observer.o') else x for x in link];link[link.index('-o')+1]=str(D/'vpr');paths=[Path(__file__),old/'protocol.json',old/'receipt.json',old/'observer.cpp',op,R/'experiments/prince_query_ledger_join_v1_2026-10-20/research_decision_v1.json',*[Path(x) for x in link if not x.startswith('-') and Path(x).is_file() and x!=str(D/'observer.o')]];bindings={str(x):sha(x) for x in paths};(D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Same owned connection/restore objects and live ledger. If explicit identity env enabled, CHANNEL cost returned from conditional present F=live O-I, with bit equality assertion against original call. Base/history unchanged. NonCHANNEL forwards original. Unsupported CHANNEL capacity/nonconfigurable group fails closed. No future predictor.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as f:code=subprocess.call(cmd,cwd=D,stdout=f,stderr=subprocess.STDOUT)
  print(name,code,flush=True)
  if code:raise SystemExit(code)
 assert all(sha(x)==h for x,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(D/'vpr'),bindings={str(x):sha(x) for x in [D/'protocol.json',op,D/'observer.o']}),indent=2)+'\n')
if __name__=='__main__':main()
