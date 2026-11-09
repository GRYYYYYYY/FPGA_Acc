"""Fixed ascending-NET residual-capacity construction; diagnostic RC relaxation."""
import pathlib,json,hashlib,time
from array import array
from collections import Counter
from MMC_zero_node_RC_shared_CSR_v1 import load
from shortest_NET_tree_csr_certified_v2 import prepare_csr
from shortest_NET_tree_ensemble_v1 import materialize
from coupled_NET_tree_candidates_csr_v2 import CSRIndex,tree_candidate
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_residual_capacity_group_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 O.mkdir(exist_ok=False);prior=R/'experiments/mmc_complete_tree_bank_csr_v2_2026-10-19';proof=prior/'independent_XML_verification_v1.json';proofdata=json.loads(proof.read_text());assert proofdata['status']=='ALL10_COMPLETE_TREES_XML_RC_UNIQUE_NET_OCCUPANCY_AND_ALL32_CHOICES_PASS'
 for p,h in proofdata['bindings'].items():assert sha(pathlib.Path(p))==h
 graph=next(pathlib.Path(p) for p in proofdata['bindings'] if p.endswith('rr_graph.xml'));nets=[1395,1400,1404,1754,2925];bindings={str(p):sha(p) for p in [proof,graph,pathlib.Path(__file__).resolve(),R/'tools/coupled_NET_tree_candidates_csr_v2.py',R/'tools/shortest_NET_tree_csr_certified_v2.py',R/'tools/shortest_NET_tree_ensemble_v1.py']}
 for net in nets:
  p=prior/f'net_{net}_original.json';bindings[str(p)]=sha(p)
 write(O/'protocol.json',dict(bindings=bindings,NET_order=nets,external_occupancy='zero; isolated known-development group',policy='One ascending NET order, no reroute or order search. Each NET is shortest in graph with all prefix-saturated nodes deleted; lexicographically first supported parent tree; commit once per NET/node.',RC_policy='Diagnostic construction permits observed RC relaxation, reports original fixed-budget violations. Actual constrained minima are used only to audit physical paths, not to replace original accepted budgets.',scope='Full MMC capacity, original quality, native utility and end-to-end gains remain unproven.'))
 offsets,dest,cost,caps,kinds,seconds=load(graph);index=CSRIndex(offsets,dest,cost,caps,kinds);occupancy=Counter();rows=[];complete=True
 for net in nets:
  q=json.loads((prior/f'net_{net}_original.json').read_text());source=q['source'];sinks=sorted(map(int,q['paths']));floor={int(s):v for s,v in q['sink_floors'].items()};budget={int(s):v for s,v in q['sink_budgets'].items()};blocked=sorted(v for v,n in occupancy.items() if n==caps[v]);local=array('I',caps)
  for v in blocked:local[v]=0
  write(O/f'net_{net}_input.json',dict(net_id=net,source=source,sinks=sinks,prefix_saturated_nodes=blocked,original_floors=floor,original_budgets=budget))
  start=time.monotonic()
  if local[source]==0 or any(local[s]==0 for s in sinks):status='PREFIX_TERMINAL_CAPACITY_BLOCKED';p=None
  else:
   try:p=prepare_csr(offsets,dest,cost,local,kinds,source,sinks);status='DIAGNOSTIC_TREE_COMMITTED'
   except ValueError:p=None;status='UNREACHABLE_SINK_UNDER_FIXED_PREFIX'
  if p is None:
   rows.append(dict(net_id=net,status=status,seconds=time.monotonic()-start));complete=False;break
  tree=materialize(p,{v:min(ps) for v,ps in p['choices'].items()});actual={s:p['distance'][s][0] for s in sinks};candidate=tree_candidate(index,source,tree['paths'],floor,actual)
  assert all(occupancy[v]+1<=caps[v] for v in candidate['nodes']);assert not set(blocked)&candidate['nodes']
  # Only commit after complete-path admission; each shared tree node counted once.
  occupancy.update(candidate['nodes'])
  for key in ['potential_cost','potential_hops']:(O/f'net_{net}_{key}.bin').write_bytes(p[key].tobytes())
  write(O/f'net_{net}_tree.json',dict(net_id=net,source=source,paths=tree['paths'],unique_nodes=sorted(candidate['nodes']),sink_labels={s:p['distance'][s] for s in sinks},excess=candidate['excess']))
  violations={s:actual[s]-budget[s] for s in sinks if actual[s]>budget[s]};row=dict(net_id=net,status=status,sinks=len(sinks),unique_nodes=len(candidate['nodes']),prefix_saturated_nodes=len(blocked),original_budget_violations=len(violations),maximum_budget_excess_units_1e18=max(violations.values(),default=0),sum_sink_RC_increase_units_1e18=candidate['excess'],seconds=time.monotonic()-start);rows.append(row);print(row,flush=True)
 write(O/'final_unique_NET_occupancy.json',dict(sorted(occupancy.items())))
 write(O/'results.json',dict(status='FIXED_ORDER_FIVE_NET_DIAGNOSTIC_CONSTRUCTION_COMPLETE' if complete else 'FIXED_ORDER_PREFIX_BLOCKED_NO_GLOBAL_INFEASIBILITY_CLAIM',graph_load_seconds=seconds,rows=rows,all_five_committed=complete,all_original_RC_budgets_pass=complete and all(row['original_budget_violations']==0 for row in rows),independent_XML_and_global_potential_audit_pending=True));print('ALL5',complete,flush=True)
if __name__=='__main__':main()
