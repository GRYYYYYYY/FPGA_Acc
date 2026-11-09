"""Actual full12 original-budget execution entries; supplied native commands remain unlaunched."""
import json,time
from pathlib import Path
from strict_budget_workflow_entry_v2 import execute
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/strict_budget_cohort_entry_v2_2026-10-08';D.mkdir(exist_ok=False)
B=R/'experiments/branch_budget_admission_census_v1_2026-10-08'
P=R/'experiments/retained_seed_session_native_cohort_v3_2026-10-08/protocol.json'
plans=json.loads(P.read_text())['plans'];cases=json.loads((B/'protocol.json').read_text())['cases']
bindings={str(P):sha(P),str(B/'protocol.json'):sha(B/'protocol.json')}
for n in ('trial_strict_budget_cohort_entry_v2.py','strict_budget_workflow_entry_v2.py','certified_budget_execution_gate_v2.py','pre_route_endpoints.py'):
 f=R/'tools'/n;bindings[str(f)]=sha(f)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='All12 original-budget actual execute entry with supplied native command and planned isolated working directory; prior independently verified floor cache. No seed preparation or candidate construction before admission. Cache production excluded, not routing speedup.'),indent=2)+'\n')
start=time.perf_counter();rows=[]
for c in cases:
 plan=next(p for p in plans if (p['width'],p['index'])==(c['width'],c['index']))
 name=f'w{c["width"]}_m{c["index"]}'
 report=execute(B/(name+'_admission.json'),B/'verification.json',c['target'],c['budget'],plan['command'],D/(name+'_candidate'),D/name)
 assert not report['candidate_launched'] and report['candidate_exit_code'] is None
 assert report['decision']=='SKIP_CERTIFIED_MODEL_INFEASIBLE' and not (D/(name+'_candidate')).exists()
 rows.append(dict(width=c['width'],index=c['index'],**report));print(name,'certified skip',flush=True)
assert len(rows)==12
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,entry_component_seconds=time.perf_counter()-start,candidate_launches=0,scope='All12 actual original-budget entries, no candidate working directory/log or native outputs; exact model infeasibility only. No quality acceptance, no fresh floor generation, no native runtime-gain claim.'),indent=2)+'\n')
