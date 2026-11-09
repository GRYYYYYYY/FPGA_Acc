"""Deterministic real mixed-NET primary comparison at a common frozen snapshot."""
import json,sys,time,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from criticality_shared_tree_sparse_reference_v3 import Graph
from criticality_retained_net_primary_v1 import route as retained
from criticality_ordered_net_primary_v1 import route as control
from load_initial_connection_criticalities_v1 import load as load_criticalities
from load_structural_node_base_v1 import load as load_base
from criticality_objective_admission_v1 import prepare
O=R/'experiments/mmc_selective_tree_preflight_v1_2026-10-13';proof=O/'retained_tree_import_trial_v1.json';v=json.loads(proof.read_text());bindings={**v['bindings'],**closure([Path(__file__)]),str(proof):sha(proof)};assert all(sha(k)==h for k,h in bindings.items())
census=json.loads((O/'estimator_round0_eligibility_v1.json').read_text());selected=min((r for r in census['pernet'] if r['fanout']>=16 and 0<r['clean_connections']<r['fanout']),key=lambda r:(r['fanout'],r['net']));net=selected['net']
ep=next(Path(k) for k in bindings if k.endswith('/endpoints.json'));graph,digest,nodes,f,rc,queries=load_endpoints(ep);g=Graph(f,rc.increments,[rc.initial(u) for u in range(len(f['capacities']))]);slots={eid:i for i,eid in enumerate(f['edge_ids'])}
state=json.loads((R/'experiments/mmc_delayed_history_ablation_v1_2026-10-13/model/round0.json').read_text());qs=[q for q in queries if q['net_id']==net];old=[r for r in state['records'] if r['net_id']==net];ledger={int(k):v for k,v in state['ledger'].items()};criticalities=load_criticalities(R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10');cp=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10/verification.json';bindings.update(json.loads(cp.read_text())['bindings']);bindings[str(cp)]=sha(cp);base,bb=load_base(len(f['capacities']),rc.scale);bindings.update(bb)
owned={r['source'] for r in old}|{f['dest_ranks'][slots[e]] for r in old for e in r['answer']['physical_edge_ids']};span={int(k):v for k,v in state['prices'].items()};weight=rc.scale//(20*10**9)
class Prices:
 def get(self,n,default=0):
  history=max(0,ledger.get(n,0)-f['capacities'][n]);other=ledger.get(n,0)-(n in owned);present=max(0,other-f['capacities'][n]+1)
  return base[n]*(1+history)*(1+present)+span.get(n,0)*weight
prices=Prices();results={};frozen=copy.deepcopy(old)
for label,fn in [('control',control),('retained',retained)]:
 tick=time.perf_counter();a=fn(g,qs,old,criticalities,prices,f['edge_ids'],ledger,f['capacities'],slots) if label=='retained' else fn(g,qs,old,criticalities,prices,f['edge_ids']);seconds=time.perf_counter()-tick
 assert old==frozen
 row=dict(complete=a['complete'],seconds=seconds,search_calls=a.get('search_calls',len(a['search_results'])),retained_connection_ids=a.get('retained_connection_ids',[]))
 if a['complete']:
  answers={r['connection_id']:r for r in a['search_results']};attempts={r['connection_id']:r['physical_edge_ids'] for r in a['attempts']};candidate=[dict(r,answer=dict(r['answer'],physical_edge_ids=attempts[r['connection_id']],delay=answers[r['connection_id']]['raw'])) for r in old];plan=prepare(f,rc,slots,qs,old,candidate,ledger,criticalities,prices);row.update(admission_status=plan['status'],objective_delta=str(plan['objective_delta']),overflow_delta=plan['prospective_overflow_delta'])
 results[label]=row
assert all(sha(k)==h for k,h in bindings.items());(O/'real_primary_pair_trial_v1.json').write_text(json.dumps(dict(bindings=bindings,selected=selected,results=results,scope='One deterministic smallest mixed threshold NET common-snapshot primary trial; wholeNET physical/objective/overflow proposal validation, no fallback/fullschedule or end-to-end speed proof.'),indent=2)+'\n');print(net,results,flush=True)
