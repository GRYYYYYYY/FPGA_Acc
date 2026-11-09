"""Independent tokenized log-counter replay and an exact observed fee ceiling."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'declared_mux_native_work_v1_2026-10-08';dp=D/'diagnosis.json';d=json.loads(dp.read_text());assert all(sha(p)==h for p,h in d['bindings'].items());checks=0
for row in d['rows']:
 for arm,dirname in [('seed','retained_seed_session_native_cohort_v2_2026-10-08'),('cold','declared_mux_cold_native_cohort_v1_2026-10-08')]:
  p=E/dirname/f'w{row["width"]}_m{row["index"]}/run.log';lines=p.read_text().splitlines();iterrows=[];summary=None
  for line in lines:
   parts=line.split()
   if len(parts)>8 and parts[0].isdigit() and parts[3:8] and all(x.isdigit() for x in parts[3:8]) and parts[8]=='(':
    iterrows.append(tuple(int(parts[i]) for i in (0,4,5,6,7)))
   if line.startswith('Router Stats:'):
    assert summary is None;summary={parts[i].rstrip(':'):int(parts[i+1]) for i in range(2,10,2)}
  assert iterrows and [x[0] for x in iterrows]==list(range(1,len(iterrows)+1))
  expected=row[arm]
  assert len(iterrows)==expected['iterations']
  assert sum(x[1] for x in iterrows)==summary['total_heap_pushes']==expected['heap_pushes']
  assert sum(x[2] for x in iterrows)==summary['total_nets_routed']==expected['nets_routed_attempts']
  assert sum(x[3] for x in iterrows)==summary['total_connections_routed']==expected['connection_routing_attempts']
  assert summary['total_heap_pops']==expected['heap_pops'];checks+=1
wp=E/'declared_mux_session_comparison_v1_2026-10-08/receipt.json';w=json.loads(wp.read_text());seed=w['arms']['seed'];cold=w['arms']['cold'];native=next(x for x in seed['stages'] if x['script']=='trial_retained_seed_session_native_cohort_v2.py')['elapsed_seconds']
optimistic=seed['declared_cohort_seconds']-native
assert optimistic>cold['declared_cohort_seconds']
report=dict(bindings={**d['bindings'],str(dp):sha(dp),str(wp):sha(wp),str(Path(__file__)):sha(Path(__file__))},independent_log_counter_replays=checks,all12_less_connection_attempts=True,all12_less_heap_pushes=True,seed_declared_seconds=seed['declared_cohort_seconds'],cold_declared_seconds=cold['declared_cohort_seconds'],seed_native_stage_seconds=native,counterfactual_zero_seed_native_stage_seconds=optimistic,counterfactual_still_slower=True,scope='Exact arithmetic of this observed boundary holding all other seed costs fixed, even entire native stage including copies/startup/output hashing set to zero. Not an executed workflow, deletion of checks, a universal runtime lower bound, or unseen-family result. Counter decrease is genuine across all archived cases; it does not imply total workflow gain.')
assert checks==24 and all(sha(p)==h for p,h in report['bindings'].items())
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='bindings'})
