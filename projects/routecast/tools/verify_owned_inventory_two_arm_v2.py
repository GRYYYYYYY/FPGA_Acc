"""Authenticate whole two-arm clocks and paired input/QoR rows."""
import json
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/owned_inventory_two_arm_v2_2026-10-08'
r=json.loads((D/'receipt.json').read_text());assert r['protocol_sha256']==sha(D/'protocol.json');bindings={}
for arm in ('seed','cold'):
 for file in ('receipt.json','verification.json'):
  p=D/arm/file;v=json.loads(p.read_text());assert all(sha(f)==h for f,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
 assert all(x['exit_code']==0 for x in r['arms'][arm]['stages'])
 assert sum(x['seconds'] for x in r['arms'][arm]['stages'])<=r['arms'][arm]['declared_seconds']
s=json.loads((D/'seed/receipt.json').read_text());c=json.loads((D/'cold/receipt.json').read_text());rows=[]
assert len(s['rows'])==len(c['rows'])==12
for a,b in zip(s['rows'],c['rows']):
 assert (a['width'],a['index'])==(b['width'],b['index']) and a['command']==b['command']
 rows.append(dict(width=a['width'],index=a['index'],seed_violations=a['violation_ids'],cold_violations=b['violation_ids'],joint_printed_nonregression=Fraction(a['cpd_ns'])<=Fraction(b['cpd_ns']) and a['wirelength']<=b['wirelength']))
for f in (D/'receipt.json',D/'protocol.json',Path(__file__)):bindings[str(f)]=sha(f)
assert all(sha(f)==h for f,h in bindings.items())
seed=r['arms']['seed']['declared_seconds'];cold=r['arms']['cold']['declared_seconds']
report=dict(bindings=bindings,rows=rows,seed_seconds=seed,cold_seconds=cold,observed_seed_over_cold=seed/cold,observed_time_gain=seed<cold,original_budget_admitted_cases={'seed':s['original_budget_admitted_cases'],'cold':c['original_budget_admitted_cases']},printed_joint_nonregression_cases=sum(x['joint_printed_nonregression'] for x in rows),scope='Fresh sequential same provided-input cohort, actual24 native runs and all complete physical/originalbudget proofs plus external frozen archive parity stages timed. No repeat/order reversal, original input generation, canonical pin/HDL equivalence or unseen-family gain.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ('bindings','rows')})
