"""Native identity/route vs prepared endpoint guards across three placements."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from live_endpoint_binding_v3 import validate
out=R/'experiments/native_live_endpoint_binding_v3_2026-10-07';out.mkdir();eps=[R/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json' for i in (1,2,3)];ctx=ReusableRRFloors(eps[0],R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',out/'context');inv=SharedRRInventory(ctx);rows=[];inputs={str(p):sha(p) for p in eps}
for i in (1,2,3):
 w=R/f'experiments/native_live_search_move_sequence_v5_2026-10-07/step_{i}/native';identity=w/'live.identity.jsonl';route=w/'live.route';inputs.update({str(p):sha(p) for p in (identity,route)})
 for j,ep in enumerate(eps,1):
  try:count=validate(ep,identity,inv,route);error=None
  except ValueError as e:count=None;error=str(e)
  assert (error is None)==(i==j),(i,j,error);assert count==516 if i==j else 'site/class mismatch' in error
  rows.append(dict(identity_step=i,endpoint_step=j,accepted=error is None,error=error))
identity=R/'experiments/native_live_search_move_sequence_v5_2026-10-07/step_3/native/live.identity.jsonl';route=identity.parent/'live.route';meta=json.loads(eps[2].read_text())
for case in ('missing_sink','missing_whole_net','duplicate_connection'):
 m=json.loads(json.dumps(meta))
 if case=='missing_sink':m['connections'].pop()
 if case=='missing_whole_net':nid=m['connections'][0]['net_id'];m['connections']=[q for q in m['connections'] if q['net_id']!=nid]
 if case=='duplicate_connection':m['connections'].append(m['connections'][0])
 ep=out/(case+'.json');ep.write_text(json.dumps(m));error=None
 try:validate(ep,identity,inv,route)
 except ValueError as e:error=str(e)
 assert error,(case,error);rows.append(dict(case=case,accepted=False,error=error))
assert all(sha(p)==h for p,h in inputs.items());(out/'receipt.json').write_text(json.dumps(dict(inputs=inputs,rows=rows,source_sha256=sha(R/'tools/native_route_transaction/live_endpoint_binding_v3.py'),checker_sha256=sha(__file__),scope='3 genuine native live tables/route dumps x 3 placements: exact matching diagonal accepted, all six cross-place contexts rejected. Missing sink/whole routed NET/duplicate pin rejected. Global unrouted clock excluded by actual route path coverage, not guessed from metadata NET names.'),indent=2)+'\n');print('PASS',len(rows))
