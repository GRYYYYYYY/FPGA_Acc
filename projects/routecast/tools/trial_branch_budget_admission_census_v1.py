"""Fixed 12-case census; sequential complete floors/proofs/admission, no quality-driven selection."""
import json,subprocess,sys
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
P=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json';cases=json.loads(P.read_text())['cases'];assert {(c['width'],c['index']) for c in cases}=={(w,i) for w in (8,16,32) for i in range(4)} and len(cases)==12
D=R/'experiments/branch_budget_admission_census_v1_2026-10-08';D.mkdir(exist_ok=False)
bindings={str(P):sha(P),**closure([Path(__file__),R/'tools/native_resume_prototype/estimate_branch_budget_cohort_floors_v2.py',R/'tools/native_resume_prototype/verify_branch_budget_cohort_floors_v2.py',R/'tools/admit_certified_route_budgets_v1.py'])}
for c in cases:
 for k in ('target','budget'):bindings[c[k]]=sha(c[k])
prior={(16,1):R/'experiments/native_resume_target_rr_floors_w16_m1_2026-10-07',(32,3):R/'experiments/native_resume_target_rr_floors_w32_m3_2026-10-07',(32,2):R/'experiments/branch_budget_target_rr_floors_w32_m2_2026-10-08'}
for f in prior.values():
 for n in ('receipt.json','verification.json','protocol.json'):bindings[str(f/n)]=sha(f/n)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,policy='All fixed 12 known development cases, unchanged exact budgets; existing certified 3 cohorts reused only for admission census, not performance timing. New 9 cohorts complete sequential floor proofs, no quality/run-time filtering.'),indent=2)+'\n')
rows=[]
for c in cases:
 w,i=c['width'],c['index'];f=prior.get((w,i),R/f'experiments/branch_budget_cohort_rr_floors_w{w}_m{i}_2026-10-08')
 if (w,i) not in prior:
  for stage,script in [('producer','estimate_branch_budget_cohort_floors_v2.py'),('verifier','verify_branch_budget_cohort_floors_v2.py')]:
   with (D/f'w{w}_m{i}_{stage}.log').open('w') as log:
    code=subprocess.run(['python3',str(R/'tools/native_resume_prototype'/script),str(w),str(i)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
   print(w,i,stage,'exit',code,flush=True)
   if code:raise SystemExit(code)
 admission=D/f'w{w}_m{i}_admission.json'
 result=subprocess.run(['python3',str(R/'tools/admit_certified_route_budgets_v1.py'),'--endpoints',c['target'],'--budget',c['budget'],'--floors',str(f),'--output',str(admission)],cwd=R)
 if result.returncode:raise SystemExit(result.returncode)
 a=json.loads(admission.read_text());rows.append(dict(width=w,index=i,connections=a['connections'],admitted=a['admitted'],blockers=[x['connection_id'] for x in a['blockers']],admission_path=str(admission),admission_sha256=sha(admission)))
 (D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(sha(f)==h for f,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(D/'protocol.json'),rows=rows,complete_cases=12,admitted_cases=sum(x['admitted'] for x in rows),scope='Complete admission census only; not end-to-end performance or heldout validation'),indent=2)+'\n');print('complete census',sum(x['admitted'] for x in rows),'admitted / 12',flush=True)
