"""Fixed ascending-NET residual-capacity construction; diagnostic RC relaxation."""
import pathlib,json,hashlib,time
from array import array
from collections import Counter
from MMC_zero_node_RC_shared_CSR_v1 import load
from shortest_NET_tree_csr_certified_v2 import prepare_csr
from shortest_NET_tree_ensemble_v1 import materialize
from coupled_NET_tree_candidates_csr_v2 import CSRIndex,tree_candidate
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_prior_native_coordinate_reopt_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 O.mkdir(exist_ok=False);prior=R/'experiments/mmc_prior_native_budget_bank_v1_2026-10-19';proof=prior/'independent_verification_v1.json';proofdata=json.loads(proof.read_text());assert proofdata['status']=='PRIOR_NATIVE_BUDGETS_PHYSICALLY_WITNESSED_AND_BOTH_BANK_OPTIMA_ENUMERATED'
 for p,h in proofdata['bindings'].items():assert sha(pathlib.Path(p))==h
 graph=next(pathlib.Path(p) for p in proofdata['bindings'] if p.endswith('rr_graph.xml'));nets=[1395,1400,1404,1754,2925];bindings={str(p):sha(p) for p in [proof,graph,pathlib.Path(__file__).resolve(),R/'tools/coupled_NET_tree_candidates_csr_v2.py',R/'tools/shortest_NET_tree_csr_certified_v2.py',R/'tools/shortest_NET_tree_ensemble_v1.py']}
 sourceframe=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';bindings[str(sourceframe)]=sha(sourceframe)
 for net in nets:
  p=prior/f'net_{net}_prior_native.json';bindings[str(p)]=sha(p)
 write(O/'protocol.json',dict(bindings=bindings,NET_order=nets,external_occupancy='all other55300 NETs from certified full prior native state; remove only current NET before search',policy='Exactly one ascending pass over five previously fixed unchanged NETs. Remove current old tree, retain all other NETs, compute residual lex minima, commit once per node only after full physical/RC admission; no iteration or ordering search.',RC_policy='Enforce fixed exact prior-native per-connection RC budgets. Old tree witnesses residual feasibility at every step; no budget relaxation is allowed.',scope='Full physical occupancy is for old-source endpoint context with five unchanged NETs reoptimized; not a complete new-placement route, new native FULL/STA, predictor quality or end-to-end gain.'))
 offsets,dest,cost,caps,kinds,seconds=load(graph);index=CSRIndex(offsets,dest,cost,caps,kinds);sourceframe=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';frame=json.loads(sourceframe.read_text());occupancy=Counter({int(v):n for v,n in frame['ledger'].items()});rows=[];complete=True
 for net in nets:
  q=json.loads((prior/f'net_{net}_prior_native.json').read_text());occupancy.subtract(q['unique_nodes']);assert all(n>=0 for n in occupancy.values());source=q['source'];sinks=sorted(map(int,q['paths']));floor={int(s):v for s,v in q['sink_floors'].items()};budget={int(s):v for s,v in q['sink_budgets'].items()};blocked=sorted(v for v,n in occupancy.items() if n==caps[v]);local=array('I',caps)
  for v in blocked:local[v]=0
  write(O/f'net_{net}_input.json',dict(net_id=net,source=source,sinks=sinks,prefix_saturated_nodes=blocked,original_floors=floor,original_budgets=budget))
  start=time.monotonic()
  if local[source]==0 or any(local[s]==0 for s in sinks):status='PREFIX_TERMINAL_CAPACITY_BLOCKED';p=None
  else:
   try:p=prepare_csr(offsets,dest,cost,local,kinds,source,sinks);status='PRIOR_BUDGET_TREE_COMMITTED'
   except ValueError:p=None;status='UNREACHABLE_SINK_UNDER_FIXED_PREFIX'
  if p is None:
   raise AssertionError('Old native witness guarantees residual budget feasibility: '+status)
  tree=materialize(p,{v:min(ps) for v,ps in p['choices'].items()});actual={s:p['distance'][s][0] for s in sinks};candidate=tree_candidate(index,source,tree['paths'],floor,budget);assert all(actual[s]<=budget[s] for s in sinks)
  assert all(occupancy[v]+1<=caps[v] for v in candidate['nodes']);assert not set(blocked)&candidate['nodes']
  # Only commit after complete-path admission; each shared tree node counted once.
  occupancy.update(candidate['nodes'])
  for key in ['potential_cost','potential_hops']:(O/f'net_{net}_{key}.bin').write_bytes(p[key].tobytes())
  write(O/f'net_{net}_tree.json',dict(net_id=net,source=source,paths=tree['paths'],unique_nodes=sorted(candidate['nodes']),sink_labels={s:p['distance'][s] for s in sinks},excess=candidate['excess']))
  violations={s:actual[s]-budget[s] for s in sinks if actual[s]>budget[s]};row=dict(net_id=net,status=status,sinks=len(sinks),unique_nodes=len(candidate['nodes']),prefix_saturated_nodes=len(blocked),original_budget_violations=len(violations),prior_native_sum_RC_units_1e18=sum(budget.values()),new_sum_RC_units_1e18=sum(actual.values()),strictly_improved_sink_paths=sum(actual[s]<budget[s] for s in sinks),maximum_budget_excess_units_1e18=max(violations.values(),default=0),sum_sink_RC_increase_units_1e18=candidate['excess'],seconds=time.monotonic()-start);rows.append(row);print(row,flush=True)
 write(O/'final_unique_NET_occupancy.json',{v:n for v,n in sorted(occupancy.items()) if n})
 write(O/'results.json',dict(status='FIXED_PASS_PRIOR_NATIVE_BUDGET_REOPTIMIZATION_COMPLETE' if complete else 'FIXED_ORDER_PREFIX_BLOCKED_NO_GLOBAL_INFEASIBILITY_CLAIM',graph_load_seconds=seconds,rows=rows,all_five_committed=complete,all_original_RC_budgets_pass=complete and all(row['original_budget_violations']==0 for row in rows),independent_XML_and_global_potential_audit_pending=True));print('ALL5',complete,flush=True)
if __name__=='__main__':main()
