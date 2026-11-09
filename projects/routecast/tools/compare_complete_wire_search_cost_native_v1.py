"""Authenticate two complete component observations, without a paired speed claim."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/complete_wire_search_cost_comparison_native_v1_2026-10-08';D.mkdir(exist_ok=False)
bindings={str(Path(__file__)):sha(Path(__file__))};observations=[];receipts=[]
for suffix in ('v2','native_v1'):
 directory=R/f'experiments/complete_wire_search_cost_replay_{suffix}_2026-10-08';vp=directory/'verification.json';rp=directory/'receipt.json';v=json.loads(vp.read_text());r=json.loads(rp.read_text())
 assert v['all_complete_cohort_fidelity_and_cost_arithmetic_checks_pass'] and v['complete_events']==5787 and v['search_calls']==5781 and all(sha(f)==h for f,h in v['bindings'].items())
 bindings.update(v['bindings']);bindings[str(vp)]=sha(vp);bindings[str(rp)]=sha(rp)
 observations.append(v);receipts.append(r)
for left,right in zip(receipts[0]['complete_passes'],receipts[1]['complete_passes']):
 assert left['name']==right['name'] and left['initial_wire']==right['initial_wire'] and left['final_wire']==right['final_wire'] and len(left['rows'])==len(right['rows'])==1929
 for a,b in zip(left['rows'],right['rows']):
  keys=('connection_id','status','searched','labels_created','labels_expanded','examined_edges')
  assert {k:a[k] for k in keys if k in a}=={k:b[k] for k in keys if k in b}
for a,b in zip(observations[0]['passes'],observations[1]['passes']):
 for key in ('name','search_calls','labels_created','labels_expanded','examined_edges','status_counts'):assert a[key]==b[key]
assert all(sha(f)==h for f,h in bindings.items())
rows=[]
for name,v in zip(('python_incremental_ledger','native_cpu_incremental_ledger'),observations):
 rows.append(dict(implementation=name,search_seconds=v['total_search_seconds'],maintenance_seconds=v['total_maintenance_seconds'],context_seconds=v['context_seconds'],component_elapsed_seconds=v['elapsed_seconds']))
out=dict(bindings=bindings,all5787_events_and5781_search_work_counters_identical=True,observations=rows,observed_maintenance_seconds_reduction=rows[0]['maintenance_seconds']-rows[1]['maintenance_seconds'],observed_component_seconds_reduction=rows[0]['component_elapsed_seconds']-rows[1]['component_elapsed_seconds'],paired_speedup_proved=False,end_to_end_gain_proved=False,scope='One complete component observation per implementation, sequential at different times, no paired repeats. All frozen search answers and all per-query work counters reproduced; native CPU search replaces Python search with exact identical results/counts; incremental ledger used on both. Timing deltas are observations, not universal speedup or full workflow gains. Model ceilings and upstream/native/audit artifacts reused, original two infeasible budgets remain.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2),flush=True)
