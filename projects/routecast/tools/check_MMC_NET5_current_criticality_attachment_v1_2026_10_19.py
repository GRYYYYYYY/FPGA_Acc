"""Same frozen NET5, existing criticality attachment, zero-congestion control."""
from pathlib import Path
from fractions import Fraction
import json,hashlib,time,resource
from MMC_zero_node_RC_shared_CSR_v1 import load
from criticality_shared_tree_sparse_reference_v3 import Graph
from load_initial_connection_criticalities_v3 import load as load_timing
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 begin=time.perf_counter();resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0));O=R/'experiments/mmc_NET5_current_criticality_attachment_v1_2026-10-19';O.mkdir(exist_ok=False);pilot=R/'experiments/mmc_existing_marginal_attachment_pilot_v1_2026-10-19/protocol.json';spec=json.loads(pilot.read_text());assert spec['net_id']==5;timing_dir=R/'experiments/mmc_current_initial_timing_snapshots_v2_2026-10-19/episode_01';tick=time.perf_counter();criticality=load_timing(timing_dir);timing_load=time.perf_counter()-tick;queries=spec['ordered_queries'];budgets={int(n):v for n,v in spec['budgets'].items()};floors={int(n):v for n,v in spec['floor_costs'].items()};ordered=[]
 for q in queries:
  c=criticality[q['connection_id']];assert (q['net_id'],q['source'],q['sink'])==(c['net'],c['source_rr'],c['target_rr']);value=Fraction(c['criticality_numerator'],c['criticality_denominator']);assert value>0;ordered.append((-value,c['local_sink_pin'],q['connection_id'],q,value))
 ordered.sort();graph=Path(next(n for n in spec['bindings'] if n.endswith('rr_graph.xml')));assert sha(graph)==spec['bindings'][str(graph)];files=[pilot,timing_dir/'verification.json',R/'tools/criticality_shared_tree_sparse_reference_v3.py',R/'tools/load_initial_connection_criticalities_v3.py',R/'tools/MMC_zero_node_RC_shared_CSR_v1.py',Path(__file__).resolve()];bindings={str(p):sha(p) for p in files};bindings[str(graph)]=sha(graph)
 (O/'protocol.json').write_text(json.dumps({'net_id':5,'connections':41,'source':spec['source'],'ordered_connection_ids':[x[2] for x in ordered],'budgets':budgets,'initial_raw_cost':0,'congestion':'exact zero on every node','objective':'Existing c*source-to-sink raw arrival + (1-c)*new-node congestion; c exact current float32 rational. Existing descending criticality/localpin/CID ordering.','expected_control_property':'All c>0 and zero congestion make objective a positive scale of raw cost, not a new congestion predictor. No timing-aware gain attribution.','scope':'Current full-graph applicability control, not matched objective ablation versus plain marginal growth or quality/speedup experiment.','bindings':bindings},indent=2)+'\n');print('CURRENT_CRITICALITY_NET5_FROZEN',flush=True)
 tick=time.perf_counter();offsets,dest,costs,caps,kinds,_=load(graph);graph_seconds=time.perf_counter()-tick;assert all(offsets[n]==offsets[n+1] for n,k in enumerate(kinds) if k=='SINK');assert all(kinds[n]!='SOURCE' and caps[n]>0 for n in dest);fields={'row_offsets':offsets,'dest_ranks':dest};tick=time.perf_counter();g=Graph(fields,costs,[0]*len(caps));tree=g.tree(spec['source']);setup=time.perf_counter()-tick;results=[];tick=time.perf_counter()
 for _,_,cid,q,c in ordered:
  before=dict(tree.parents),dict(tree.arrival);r=tree.expand(q['sink'],c,{},budgets[q['sink']]);results.append({'connection_id':cid,'query':q,'criticality':[c.numerator,c.denominator],**r})
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
  assert u==q['sink'] and raw==r['raw']==floors[u] and raw<=budgets[u];paths[q['connection_id']]=r['path_slots']
 audit_seconds=time.perf_counter()-tick;result=O/'result.json';result.write_text(json.dumps({'complete':complete,'queries_in_execution_order':results,'parents':tree.parents,'arrival':tree.arrival},indent=2)+'\n');bindings[str(result)]=sha(result);bindings[str(O/'protocol.json')]=sha(O/'protocol.json')
 (O/'verification.json').write_text(json.dumps({'status':'NET5_CURRENT_CRITICALITY_ZERO_CONGESTION_ALL41_MINIMUM_RAW_AND_BUDGET_PASS' if complete else 'NET5_CURRENT_CRITICALITY_FAILURE_PRESERVED','complete':complete,'connections_verified':len(paths),'costs_seconds':{'timing_loader_with_integrity':timing_load,'graph_load':graph_seconds,'immutable_graph_workspace':setup,'search41':search_seconds,'in_memory_path_audit':audit_seconds,'total_before_receipt':time.perf_counter()-begin},'peak_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'bindings':bindings,'independent_original_XML_output_path_audit_pending':True,'scope':'Zero-congestion raw-floor control only. No model novelty, global capacity/QoR, native route or full workflow gain.'},indent=2)+'\n');print('NET5_CURRENT_CRITICALITY_COMPLETE',complete,'paths',len(paths),flush=True)
if __name__=='__main__':main()
