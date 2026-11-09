"""Serial full reference correctness models for radix queue; no paired speed claim."""
import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/resident_radix_reference_trial_v3_2026-10-08';D.mkdir()
runner=R/'tools/run_resident_soft_demand_radix_v3.py';parity=R/'tools/verify_resident_radix_parity_v3.py';contract=R/'experiments/soft_demand_workspace_radix_contract_v3_2026-10-08/verification.json';proof=json.loads(contract.read_text());assert proof['random_graphs']==200 and proof['sequential_searches_full_raw_parent_edge_and_settled_arrays_equal']==2400 and all(sha(k)==h for k,h in proof['bindings'].items())
bindings={**closure([Path(__file__),runner,parity,R/'tools/verify_resident_demand_frame_physical_v3.py',R/'tools/verify_resident_events_round_schedule_cache_v4.py']),str(contract):sha(contract)}
endpoints={}
for name in ['xtea','8051']:
 p=R/'experiments/freecores_native_demand_v1_2026-10-08'/name/'endpoints.json';endpoints[name]=p;bindings[str(p)]=sha(p)
 for v in json.loads(p.read_text())['inputs'].values():bindings[v['path']]=v['sha256']
assert all(sha(k)==h for k,h in bindings.items());(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=['xtea','8051'],timeout_seconds=1200,scope='Full original initial/floors/two feedback rounds/complete paths and events; radix queue alone, original budgets/prices/order retained. Sequential correctness trial, not balanced performance or full native workflow. No failure/connection omission.'),indent=2)+'\n')
rows=[]
for name in ['xtea','8051']:
 destination=R/'experiments/freecores_resident_radix_v3_2026-10-08'/name
 try:
  with (D/(name+'.log')).open('w') as f:r=subprocess.run([sys.executable,str(runner),str(endpoints[name]),str(destination)],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
  assert r.returncode==0
  q=subprocess.run([sys.executable,str(parity),name],cwd=R,timeout=1200);assert q.returncode==0
  assert all(sha(k)==h for k,h in bindings.items());row=dict(name=name,status='MODEL_FULL_PARITY_PASS_PENDING_PHYSICAL_AND_EVENT_AUDITS')
 except Exception as error:
  rows.append(dict(name=name,status='FAILED_OR_TIMEOUT',error=repr(error)));(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');raise
 rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(row,flush=True)
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows),indent=2)+'\n')
