"""Authenticated fresh cold versus branch resume budget differences, all queries."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
paths=[R/f'experiments/{n}/target_budget_verification.json' for n in ('native_resume_branch_partial_v8_2026-10-08','native_cold_branch_control_v8_2026-10-08')]
proofs=[json.loads(p.read_text()) for p in paths];bindings={str(Path(__file__)):sha(Path(__file__))}
for p,d in zip(paths,proofs):
 assert all(sha(f)==h for f,h in d['bindings'].items());bindings.update(d['bindings']);bindings[str(p)]=sha(p)
assert {x['connection_id']:x['budget_ns'] for x in proofs[0]['rows']}=={x['connection_id']:x['budget_ns'] for x in proofs[1]['rows']}
f=R/'experiments/endpoint_compatible_branch_trim_v1_2026-10-08/w32_m2.json';bindings[str(f)]=sha(f);forest=json.loads(f.read_text())
kept={x['connection_id']:x for x in forest['retained']};released={x['connection_id']:x for x in forest['released']}
a,b=[{x['connection_id']:x for x in d['rows']} for d in proofs]
assert set(a)==set(b)==set(kept)|set(released)
rows=[]
for cid in sorted(a):
 if not a[cid]['budget_pass'] or not b[cid]['budget_pass']:
  rows.append(dict(connection_id=cid,seed_decision='RETAINED' if cid in kept else released[cid]['reason'],resume=a[cid],cold=b[cid]))
metrics=[]
for name,mode in [('native_resume_branch_partial_v8_2026-10-08','resume'),('native_cold_branch_control_v8_2026-10-08','cold')]:
 d=R/'experiments'/name;p=d/'receipt.json';bindings[str(p)]=sha(p);receipt=json.loads(p.read_text());log=d/mode/'run.log';bindings[str(log)]=sha(log);text=log.read_text()
 metrics.append(dict(mode=mode,cpd_ns=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1],wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]),native_process_seconds=receipt['rows'][0]['wall_seconds']))
D=R/'experiments/branch_partial_budget_regressions_v1_2026-10-08';D.mkdir(exist_ok=False)
assert all(sha(f)==h for f,h in bindings.items())
report=dict(bindings=bindings,all_queries_compared=1929,resume_failures=sum(not x['budget_pass'] for x in a.values()),cold_failures=sum(not x['budget_pass'] for x in b.values()),resume_only_failures=[cid for cid in a if not a[cid]['budget_pass'] and b[cid]['budget_pass']],cold_only_failures=[cid for cid in a if a[cid]['budget_pass'] and not b[cid]['budget_pass']],rows=rows,metrics=metrics,scope='One fresh cold and one prior resume, identical v8 options and input bytes to be independently authenticated; native clocks exclude preparation/all audits, no paired performance or infeasibility claim.')
(D/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('bindings','rows')},indent=2))
