"""Unchanged existing compiled generic-price adapter, same fixed real graph41 calls."""
from pathlib import Path
from fractions import Fraction
import json,hashlib,time,resource
from MMC_zero_node_RC_shared_CSR_v1 import load
from load_structural_node_base_v1 import load as load_base
from compiled_criticality_tree_v1 import Graph,BINARY
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
class Prices:
 def __init__(self,values):self.values=values;self.calls=0
 def get(self,node,default=0):self.calls+=1;return self.values[node]
def normalized(r):return dict(r,path_slots=list(r['path_slots'])) if 'path_slots' in r else r
def main():
 begin=time.perf_counter();resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0));O=R/'experiments/mmc_NET5_existing_compiled_criticality_comparison_v1_2026-10-19';O.mkdir(exist_ok=False);B=R/'experiments/mmc_NET5_structural_criticality_attachment_v1_2026-10-19';proof=B/'independent_verification_v1.json';v=json.loads(proof.read_text());assert v['status']=='ALL41_STRUCTURAL_XML_PATHS_BRANCH_OBJECTIVES_WHOLE_NET_SCORES_AND_BUDGETS_PASS';reference=B/'result.json';record=json.loads(reference.read_text());spec=json.loads((B/'protocol.json').read_text());contract=R/'experiments/compiled_criticality_tree_contract_v1_2026-10-15/verification.json';c=json.loads(contract.read_text());assert c['all_pass'] and c['all_results_paths_parents_arrivals_and_atomic_rejections_identical'];assert sha(BINARY)==c['bindings'][str(BINARY)]
 for p,h in c['bindings'].items():assert sha(p)==h
 graph=Path(next(p for p in spec['bindings'] if p.endswith('rr_graph.xml')));assert sha(graph)==spec['bindings'][str(graph)];tick=time.perf_counter();base,bb=load_base(904438,10**18);base_seconds=time.perf_counter()-tick;files=[proof,reference,B/'protocol.json',contract,BINARY,R/'tools/compiled_criticality_tree_v1.py',R/'tools/wide_cost_search_bridge_v2.py',R/'tools/soft_demand_cpp/criticality_tree_exact_v2.cpp',Path(__file__).resolve()];bindings={str(p):sha(p) for p in files};bindings.update(bb)
 (O/'protocol.json').write_text(json.dumps({'bindings':bindings,'reference':str(reference),'scope':'Same frozen NET5/current exact criticalities/native-base/budgets/order. Existing generic dense adapter, no new search policy. Component observation only, not paired workflow speedup.','queries':41,'rejection_checks':'First query raw budget one lattice unit below found raw; unchanged empty tree; valid next query recovers; closed graph rejects.'},indent=2)+'\n');tick=time.perf_counter();offsets,dest,costs,caps,kinds,_=load(graph);load_seconds=time.perf_counter()-tick;tick=time.perf_counter();g=Graph({'row_offsets':offsets,'dest_ranks':dest},costs,[0]*len(caps));workspace_seconds=time.perf_counter()-tick;prices=Prices(base);tree=g.tree(spec['source']);calls=[];tick=time.perf_counter()
 try:
  for i,entry in enumerate(record['queries_in_execution_order']):
   expected={k:v for k,v in entry.items() if k not in ['connection_id','query','criticality']};q=entry['query'];value=Fraction(*entry['criticality']);result=tree.expand(q['sink'],value,prices,spec['budgets'][str(q['sink'])]);assert normalized(result)==expected;calls.append(normalized(result))
   if (i+1)%10==0:print('COMPILED_NET5_PARITY',i+1,'elapsed',time.perf_counter()-tick,flush=True)
  seconds=time.perf_counter()-tick;normal_gets=prices.calls;assert tree.parents=={int(n):tuple(p) for n,p in record['parents'].items()} and tree.arrival=={int(n):a for n,a in record['arrival'].items()};stats=list(g.total_stats);first=record['queries_in_execution_order'][0];fresh=g.tree(spec['source']);before=dict(fresh.parents),dict(fresh.arrival);reject=fresh.expand(first['query']['sink'],Fraction(*first['criticality']),prices,first['raw']-1);assert reject['status']=='RETAIN_RAW_BUDGET' and not reject['committed'] and (fresh.parents,fresh.arrival)==before;recovered=fresh.expand(first['query']['sink'],Fraction(*first['criticality']),prices,spec['budgets'][str(first['query']['sink'])]);assert normalized(recovered)=={k:v for k,v in first.items() if k not in ['connection_id','query','criticality']}
 finally:g.close()
 caught=False
 try:tree.expand(0,Fraction(1),prices,0)
 except RuntimeError:caught=True
 assert caught;payload=O/'results.json';payload.write_text(json.dumps(calls,indent=2)+'\n');bindings[str(payload)]=sha(payload);bindings[str(O/'protocol.json')]=sha(O/'protocol.json')
 (O/'verification.json').write_text(json.dumps({'status':'ALL41_EXISTING_COMPILED_GENERIC_ADAPTER_FULL_RESULT_TREE_BUDGET_REJECTION_RECOVERY_PARITY_PASS','queries':41,'normal_price_getter_calls':normal_gets,'expected_dense_calls':41*len(caps),'native_stats':stats,'rejection_atomicity':True,'next_valid_query_recovers':True,'closed_graph_rejected':True,'costs_seconds':{'base_input_load':base_seconds,'graph_load':load_seconds,'compiled_graph_workspace':workspace_seconds,'all41_existing_generic_adapter_calls':seconds,'total_before_receipt':time.perf_counter()-begin},'bindings':bindings,'scope':'Same full real graph and all result fields/tree equal bound Python reference. Includes existing dense adapter cost, no workflow speed claim or production NativePrices integration.'},indent=2)+'\n');print('COMPILED_NET5_ALL41_PASS generic_seconds',seconds,'price_gets',normal_gets,flush=True)
if __name__=='__main__':main()
