"""Replay real terminal states against the reusable observation core."""
import json
from pathlib import Path
from online_conflict_core import observe_conflict,detour_options,bounded_conflict_loop
from persistent_rc_context import PersistentRCContext
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/mux_residual_failure_2026-10-06';out=ROOT/'experiments/mux_online_conflict_core_2026-10-06';out.mkdir();r=json.loads((parent/'receipt.json').read_text());rows=[];last=None
for row in r['rows']:
 if row.get('status')=='ALLOCATION_NOT_SUBMITTED':rows.append(row);continue
 w,i=row['width'],row['index'];rf=parent/f'w{w}_m{i}.json';d=json.loads(rf.read_text());pf=ROOT/f'experiments/mux_capacity_avoid_reroute_2026-10-06/w{w}_m{i}/prediction.json';assert sha(pf)==d['prediction_sha256'];candidate=json.loads(pf.read_text());af=ROOT/f'experiments/mux_capacity_budgets_2026-10-06/w{w}_m{i}.json';a=json.loads(af.read_text())
 if w!=last:ctx=PersistentRCContext(d['target']);last=w
 else:ctx.bind_endpoints(d['target'])
 restrictions={a['selected_net']:{a['forbidden_rank']}};obs=observe_conflict(ctx,candidate,restrictions,d['budget']);assert obs['status']=='OBSERVED_CONFLICT';old=d['certificates']['relaxed'];assert obs['witness']['minimum']==old['minimum'] and obs['witness']['path_nodes']==old['path_nodes'];assert obs['blockers']==d['relaxed_witness_blockers'];options=detour_options(obs,restrictions)
 for option in options:
  assert all(option[n]>=ban for n,ban in restrictions.items()) and option!=restrictions
 # Control checks use the archived incomplete candidate as a fixture, not a new route.
 def forbidden_callback(*args):raise AssertionError('unexpected callback')
 result=bounded_conflict_loop(restrictions,forbidden_callback,forbidden_callback,lambda _:None);assert result['status']=='INITIAL_ALLOCATION_REJECTED' and not result['trace']
 result=bounded_conflict_loop(restrictions,lambda *_:candidate,forbidden_callback,lambda _:(0,{}),max_attempts=1);assert result['status']=='ATTEMPT_LIMIT' and len(result['trace'])==1
 calls=[]
 def reject_new(bans):
  calls.append(bans)
  return (0,{}) if bans==restrictions else None
 result=bounded_conflict_loop(restrictions,lambda *_:candidate,lambda *_:obs,reject_new,max_attempts=3);assert result['status']=='NO_ACCEPTED_DETOUR' and len(result['trace'])==1 and len(calls)==len(options)+1
 rows.append(dict(width=w,index=i,observation_status=obs['status'],options=len(options),minimum=obs['witness']['minimum'],prediction_sha256=sha(pf),residual_sha256=sha(rf),control_checks=3));print(rows[-1],flush=True)
(out/'receipt.json').write_text(json.dumps(dict(parent_receipt_sha256=sha(parent/'receipt.json'),parent_verification_sha256=sha(parent/'verification.json'),sources={str(p):sha(p) for p in (Path(__file__),ROOT/'tools/online_conflict_core.py')},rows=rows,scope='Real-state observation replay matches independently certified residual diagnostics. Control callback checks use archived fixtures; native reroute/timing allocator integration is not yet implemented or validated.'),indent=2)+'\n')
