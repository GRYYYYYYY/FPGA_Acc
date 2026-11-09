"""Authenticate complete fresh workflow, stage gates and outer elapsed arithmetic."""
import json,math
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/fresh_history_workflow_v1_2026-10-09'
receipt=json.loads((D/'verification.json').read_text());protocol=json.loads((D/'protocol.json').read_text());progress=json.loads((D/'progress.json').read_text())
for p,h in receipt['bindings'].items():assert sha(p)==h,p
for p,h in protocol['bindings'].items():assert sha(p)==h,p
assert receipt['rows']==progress
assert len(progress)==10 and [x['index'] for x in progress]==list(range(10))
assert [x['script'] for x in progress]==protocol['manifest']['scripts']
assert all(x['exit_code']==0 and math.isfinite(x['seconds']) and x['seconds']>=0 for x in progress)
assert receipt['workflow_seconds']>=sum(x['seconds'] for x in progress)
assert receipt['scope']==protocol['manifest']['scope']
checked=[]
for directory in protocol['manifest']['directories'].values():
 path=R/'experiments'/directory
 for name in ('verification.json','independent_verification.json','receipt.json'):
  p=path/name
  if not p.exists():continue
  doc=json.loads(p.read_text())
  for filename,digest in doc['bindings'].items():assert sha(filename)==digest,filename
  checked.append(str(p))
selected=R/'experiments/fresh_history_workflow_v1_stage_2_2026-10-09/result.json'
s=json.loads(selected.read_text());assert s['result']['status']=='SAT' and len(s['paths'])==516
quality=json.loads((R/'experiments/fresh_history_workflow_v1_stage_6_2026-10-09/verification.json').read_text())
assert receipt['quality']==quality['rows'] and len(quality['rows'])==1
row=quality['rows'][0];assert row['step']==1 and row['native_and_canonical_connections']==[516,516]
assert row['exact_model_budget_pass'] and row['full_named_paths_preserved'] and row['canonical_zero_counters']
assert row['wirelength']-row['cold_wirelength']==row['wire_delta']
bindings={str(p):sha(p) for p in [D/'verification.json',D/'protocol.json',D/'progress.json',Path(__file__).resolve(),selected]}
bindings.update({name:sha(name) for name in checked})
report=dict(bindings=bindings,workflow_seconds=receipt['workflow_seconds'],sum_stage_seconds=sum(x['seconds'] for x in progress),checked_receipts=checked,quality=receipt['quality'],scope='Authentication of all executed stage receipts and frozen scripts, progress/manifest equality, ten successful stages and elapsed arithmetic; preceding independent gates audited all real paths/proofs. Single step only, no matched cold benchmark or transaction commit.')
p=D/'independent_verification.json';assert not p.exists();p.write_text(json.dumps(report,indent=2)+'\n');print(dict(workflow_seconds=report['workflow_seconds'],checked_receipts=len(checked),quality=report['quality']),flush=True)
