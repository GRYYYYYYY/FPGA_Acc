"""Complete archived MMC endpoint projection differential and local cost evidence."""
import json, sys, time
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from audit_native_route import NET
D=R/'experiments/native_endpoint_name_set_v1_2026-10-08';D.mkdir(exist_ok=False)
W=R/'experiments/ultraembedded_mmc_continuous_workflow_v4_2026-10-08'
bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/verify_ultraembedded_mmc_native_cold_v1.py',R/'tools/verify_ultraembedded_mmc_native_name_set_v2.py',W/'verification.json']}
v=json.loads((W/'verification.json').read_text());assert v['all_cases_both_complete_arms_authenticated']
for p,h in v['bindings'].items():assert sha(p)==h
def project(a,names,ep,indexed):
 if indexed:
  allowed=set(ep['net_names'].values())
  return Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in allowed)
 return Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in set(ep['net_names'].values()))
rows=[]
for arm in ['cold','seed']:
 paths=[W/arm/'native/mmc/physical_audit.json',W/arm/'native/mmc/output.route',W/arm/'demand/mmc/endpoints.json']
 for p in paths:bindings[str(p)]=sha(p)
 a=json.loads(paths[0].read_text());ep=json.loads(paths[2].read_text())
 names={int(m[1]):m[2] for line in paths[1].read_text().splitlines() if (m:=NET.match(line))}
 required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections'])
 results=[];seconds=[]
 for indexed in [False,True]:
  tick=time.perf_counter();results.append(project(a,names,ep,indexed));seconds.append(time.perf_counter()-tick)
 assert results[0]==results[1]==required and sum(required.values())==115572
 row=dict(arm=arm,physical_connections=sum(required.values()),baseline_seconds=seconds[0],candidate_seconds=seconds[1],complete_counter_parity=True)
 rows.append(row);print(json.dumps(row),flush=True)
 (D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
# Filtering, duplicates and missing identity retain identical behavior.
for names,ep,a in [({1:'x',2:'ignored'},{'net_names':{'1':'x','3':'x'}},{'connections':[dict(net_id=1,source=3,sink=4)]*2+[dict(net_id=2,source=8,sink=9)]}), ({},{'net_names':{}},{'connections':[dict(net_id=1,source=0,sink=1)]})]:
 outcomes=[]
 for indexed in [False,True]:
  try:outcomes.append(('ok',project(a,names,ep,indexed)))
  except Exception as e:outcomes.append((type(e).__name__,str(e)))
 assert outcomes[0]==outcomes[1]
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Complete authenticated archived counters only; original XML audit not rerun. Single baseline-then-candidate per arm, in-memory projection cost only, no full workflow or statistical gain claim.'),indent=2)+'\n')
