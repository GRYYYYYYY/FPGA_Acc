"""Full12 unique-NET occupancy delta versus independently archived printed audits."""
import json,hashlib
from pathlib import Path
from types import SimpleNamespace
from actual_change_physical_delta_v1_2026_10_18 import PhysicalDelta
from actual_change_budget_recheck_v1_2026_10_18 import mapped_paths,authenticate
from unified_rr_audit_inventory_v1 import read
R=Path(__file__).resolve().parents[1];D=R/'experiments/actual_change_physical_delta_v1_2026-10-18';D.mkdir(exist_ok=False);bindings={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 p=Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
cases=load(R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json')['cases'];original=load(R/'experiments/retained_seed_session_native_cohort_v3_2026-10-08/verification.json');rows=[]
for width in (8,16,32):
 cs=[c for c in cases if c['width']==width];old=load(cs[0]['old']);authenticate(old);graph=Path(old['inputs']['graph']['path']);inv=read(graph,old['graph_sha256']);route=graph.with_name('design.route');bindings[str(route)]=sha(route);state=PhysicalDelta(mapped_paths(old,route),{q['connection_id']:q for q in old['connections']},inv);before=dict(state.occupancy)
 for c in cs:
  w,i=c['width'],c['index'];target=load(c['target']);authenticate(target);out=R/f'experiments/retained_seed_session_native_cohort_v3_2026-10-08/w{w}_m{i}';reference=load(out/'original_budget_verification.json');assert original['bindings'][str(out/'original_budget_verification.json')]==bindings[str(out/'original_budget_verification.json')];bindings[str(out/'output.route')]=sha(out/'output.route')
  answer=state.evaluate(mapped_paths(target,out/'output.route'),{q['connection_id']:q for q in target['connections']},inv)
  assert answer['node_occupancy']==reference['physical']['node_occupancy'];assert answer['overflow_units']==reference['physical']['overflow_units']==0;assert dict(state.occupancy)==before
  rows.append(dict(width=w,index=i,changed_nets=len(answer['changed_nets']),changed_connections=len(answer['changed_connection_ids']),occupied_nodes=len(answer['node_occupancy']),full_printed_occupancy_equal=True,old_state_unchanged=True));print(w,i,'NET delta occupancy PASS',flush=True)
 for entry in old['inputs'].values():bindings[entry['path']]=entry['sha256']
# Synthetic shared-trunk ownership and failure rollback.
nodes={0:('SOURCE','1'),1:('CHANX','1'),2:('SINK','1'),3:('SINK','1'),4:('CHANY','1'),5:('SOURCE','1'),6:('SINK','1')};arcs={(0,1,0):0,(1,2,0):1,(1,3,0):2,(0,4,0):3,(4,2,0):4,(4,3,0):5,(5,4,0):6,(4,6,0):7}
inv=SimpleNamespace(digest='synthetic',physical=SimpleNamespace(nodes=nodes,arcs=arcs,switches={0}));queries={0:dict(net_id=0,source=0,sink=2),1:dict(net_id=0,source=0,sink=3)};paths={0:((0,None),(1,0),(2,0)),1:((0,None),(1,0),(3,0))};state=PhysicalDelta(paths,queries,inv);assert state.occupancy[1]==1
new={0:((0,None),(4,0),(2,0)),1:((0,None),(4,0),(3,0))};answer=state.evaluate(new,queries,inv);assert '1' not in answer['node_occupancy'] and answer['node_occupancy']['4']==1
negative=[]
for mode in ['missing','bad_arc','cycle','endpoint','epoch']:
 bad=dict(new);testinv=inv
 if mode=='missing':bad.pop(1)
 elif mode=='bad_arc':bad[0]=((0,None),(4,99),(2,0))
 elif mode=='cycle':bad[0]=((0,None),(4,0),(0,0),(2,0))
 elif mode=='endpoint':bad[0]=((0,None),(4,0),(3,0))
 else:testinv=SimpleNamespace(digest='stale')
 try:state.evaluate(bad,queries,testinv)
 except ValueError:negative.append(mode)
 else:raise AssertionError(mode)
 assert state.occupancy[1]==1 and 4 not in state.occupancy
for name in ['actual_change_physical_delta_v1_2026_10_18.py','verify_actual_change_physical_delta_v1_2026_10_18.py','actual_change_budget_recheck_v1_2026_10_18.py','native_route_ledger_import_compact.py','unified_rr_audit_inventory_v1.py']:
 p=R/'tools'/name;bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,negative_cases=negative,shared_trunk_count_once=True,old_net_removed_once_new_net_added_once=True,scope='Terminal-path arc/type/nonterminal-parent and unique-NET occupancy delta. Complete printed-route structure and canonical packed-pin acceptance remain separate mandatory gates. Epoch/input authentication provided by caller; no speed or native routing improvement claim.'),f,indent=2);f.write('\n')
