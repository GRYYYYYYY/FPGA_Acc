"""Same frozen NET5, current timing and existing authenticated structural base costs."""
from pathlib import Path
from fractions import Fraction
import json,hashlib,time,resource
from MMC_zero_node_RC_shared_CSR_v1 import load
from criticality_shared_tree_sparse_reference_v3 import Graph
from load_initial_connection_criticalities_v3 import load as load_timing
from load_structural_node_base_v1 import load as load_base, PROOF as BASE_PROOF
from criticality_objective_admission_v1 import prepare as admit
from multiplicative_net_congestion_v1 import cost as node_cost
class BaseView:
 def __init__(self,values):self.values=values
 def get(self,node,default=0):return self.values[node]
class IdentitySlots:
 def __init__(self,n):self.n=n
 def __contains__(self,e):return type(e) is int and 0<=e<self.n
 def __getitem__(self,e):
  if e not in self:raise KeyError(e)
  return e
class RC:
 def __init__(self,offsets,dest,costs):self.offsets=offsets;self.dest=dest;self.costs=costs
 def initial(self,source):return 0
 def increment(self,slot):return self.costs[slot]
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 begin=time.perf_counter();resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0));O=R/'experiments/mmc_NET5_structural_criticality_attachment_v1_2026-10-19';O.mkdir(exist_ok=False);pilot=R/'experiments/mmc_existing_marginal_attachment_pilot_v1_2026-10-19/protocol.json';spec=json.loads(pilot.read_text());assert spec['net_id']==5;timing_dir=R/'experiments/mmc_current_initial_timing_snapshots_v2_2026-10-19/episode_01';tick=time.perf_counter();criticality=load_timing(timing_dir);timing_load=time.perf_counter()-tick;queries=spec['ordered_queries'];budgets={int(n):v for n,v in spec['budgets'].items()};floors={int(n):v for n,v in spec['floor_costs'].items()};ordered=[]
 for q in queries:
  c=criticality[q['connection_id']];assert (q['net_id'],q['source'],q['sink'])==(c['net'],c['source_rr'],c['target_rr']);value=Fraction(c['criticality_numerator'],c['criticality_denominator']);assert value>0;ordered.append((-value,c['local_sink_pin'],q['connection_id'],q,value))
 ordered.sort();graph=Path(next(n for n in spec['bindings'] if n.endswith('rr_graph.xml')));assert sha(graph)==spec['bindings'][str(graph)];base_values,base_bindings=load_base(904438,10**18);assert json.loads(BASE_PROOF.read_text())['bindings'][str(graph)]==sha(graph);files=[BASE_PROOF,pilot,timing_dir/'verification.json',R/'tools/criticality_shared_tree_sparse_reference_v3.py',R/'tools/load_initial_connection_criticalities_v3.py',R/'tools/MMC_zero_node_RC_shared_CSR_v1.py',Path(__file__).resolve()];bindings={str(p):sha(p) for p in files};bindings.update(base_bindings);bindings[str(graph)]=sha(graph)
 (O/'protocol.json').write_text(json.dumps({'net_id':5,'connections':41,'source':spec['source'],'ordered_connection_ids':[x[2] for x in ordered],'budgets':budgets,'initial_raw_cost':0,'congestion':'Existing native structural node base; history=0, static span=0 and no other NETs; own old tree released once, no price multiplier.','objective':'Existing c*source-to-sink raw arrival + (1-c)*new-node congestion; c exact current float32 rational. Existing descending criticality/localpin/CID ordering.','expected_control_property':'Fixed preexisting raw/new-node structural tradeoff; whole-NET original objective and nonincreasing occupancy gates required. No new parameter or sampled owner selection.','scope':'Current full-graph applicability control, not matched objective ablation versus plain marginal growth or quality/speedup experiment.','bindings':bindings},indent=2)+'\n');print('CURRENT_CRITICALITY_NET5_FROZEN',flush=True)
 tick=time.perf_counter();offsets,dest,costs,caps,kinds,_=load(graph);graph_seconds=time.perf_counter()-tick;assert all(offsets[n]==offsets[n+1] for n,k in enumerate(kinds) if k=='SINK');assert all(kinds[n]!='SOURCE' and caps[n]>0 for n in dest);fields={'row_offsets':offsets,'dest_ranks':dest};tick=time.perf_counter();assert all(node_cost(base_values[n],0,0,caps[n],False,0)==base_values[n] for n in range(len(caps)));prices=BaseView(base_values);g=Graph(fields,costs,[0]*len(caps));tree=g.tree(spec['source']);setup=time.perf_counter()-tick;results=[];tick=time.perf_counter()
 for _,_,cid,q,c in ordered:
  before=dict(tree.parents),dict(tree.arrival);r=tree.expand(q['sink'],c,prices,budgets[q['sink']]);results.append({'connection_id':cid,'query':q,'criticality':[c.numerator,c.denominator],**r})
  if not r['committed']:
   assert (tree.parents,tree.arrival)==before;break
 search_seconds=time.perf_counter()-tick;tick=time.perf_counter();parents={};paths={};complete=len(results)==41 and all(r['committed'] for r in results)
 for r in results:
  if not r['committed']:continue
  q=r['query'];u=q['source'];seen={u};raw=0
  for slot in r['path_slots']:
   assert offsets[u]<=slot<offsets[u+1];v=dest[slot];assert v not in seen and caps[v]>0
   if v in parents:assert parents[v]==(u,slot)
   parents[v]=(u,slot);seen.add(v);raw+=costs[slot];u=v
  assert u==q['sink'] and raw==r['raw'] and floors[u]<=raw<=budgets[u];paths[q['connection_id']]=r['path_slots']
 audit_seconds=time.perf_counter()-tick
 witness_file=R/'experiments/mmc_NET5_existing_budget_fallback_witness_v1_2026-10-19/witness.json';witness=json.loads(witness_file.read_text());bindings[str(witness_file)]=sha(witness_file)
 old_records=[dict(q,answer={'status':'FOUND','physical_edge_ids':witness['paths'][str(q['sink'])],'delay':floors[q['sink']]},budget_integer=budgets[q['sink']],floor_integer=floors[q['sink']]) for q in queries]
 candidate=[dict(q,answer={'status':'FOUND','physical_edge_ids':list(paths[q['connection_id']]),'delay':next(r['raw'] for r in results if r['connection_id']==q['connection_id'])},budget_integer=budgets[q['sink']],floor_integer=floors[q['sink']]) for q in queries] if complete else []
 gate=None
 if complete:
  fields.update(capacities=caps,edge_ids=range(len(dest)));ledger={n:1 for n in witness['unique_nodes']};gate=admit(fields,RC(offsets,dest,costs),IdentitySlots(len(dest)),queries,old_records,candidate,ledger,criticality,prices)
  gate={k:(str(gate[k]) if k in ['old_score','candidate_score','objective_delta'] else gate[k]) for k in ['accepted','status','old_score','candidate_score','objective_delta','prospective_overflow_delta']}
 result=O/'result.json';result.write_text(json.dumps({'complete':complete,'whole_NET_admission':gate,'queries_in_execution_order':results,'parents':tree.parents,'arrival':tree.arrival},indent=2)+'\n');bindings[str(result)]=sha(result);bindings[str(O/'protocol.json')]=sha(O/'protocol.json')
 (O/'verification.json').write_text(json.dumps({'status':'NET5_STRUCTURAL_CRITICALITY_ALL41_RAW_BUDGET_PASS_WHOLE_NET_GATE_RECORDED' if complete else 'NET5_STRUCTURAL_CRITICALITY_FAILURE_PRESERVED','complete':complete,'connections_verified':len(paths),'costs_seconds':{'timing_loader_with_integrity':timing_load,'graph_load':graph_seconds,'immutable_graph_workspace':setup,'search41':search_seconds,'in_memory_path_audit':audit_seconds,'total_before_receipt':time.perf_counter()-begin},'peak_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'bindings':bindings,'independent_original_XML_output_path_audit_pending':True,'scope':'Existing structural-cost single-NET applicability only; whole-NET objective result distinct from branch success. No model novelty, global capacity/QoR, native route or full workflow gain.'},indent=2)+'\n');print('NET5_CURRENT_CRITICALITY_COMPLETE',complete,'paths',len(paths),flush=True)
if __name__=='__main__':main()
