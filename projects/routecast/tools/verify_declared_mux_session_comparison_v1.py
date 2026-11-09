"""Authenticate both fresh12-case clocks, input parity, failures and native results."""
import json
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'declared_mux_session_comparison_v1_2026-10-08';bindings={}
def read(p):
 d=json.loads(p.read_text())
 for f,h in d.get('bindings',{}).items():
  assert sha(f)==h,f
  assert f not in bindings or bindings[f]==h
  bindings[f]=h
 bindings[str(p)]=sha(p);return d
r=read(D/'receipt.json');p=read(D/'protocol.json');assert r['protocol_sha256']==sha(D/'protocol.json')
for arm in ('seed','cold'):
 stages=r['arms'][arm]['stages'];assert [x['script'] for x in stages]==p['arms'][arm]
 assert all(x['exit_code']==0 for x in stages) and sum(x['elapsed_seconds'] for x in stages)<=r['arms'][arm]['declared_cohort_seconds']
 for x in stages:log=D/f'{arm}_{x["script"]}.log';bindings[str(log)]=sha(log)
sd=E/'retained_seed_session_native_cohort_v2_2026-10-08';cd=E/'declared_mux_cold_native_cohort_v1_2026-10-08'
s=read(sd/'verification.json');c=read(cd/'verification.json');sp=read(sd/'protocol.json');cp=read(cd/'protocol.json');sr=read(sd/'receipt.json');cr=read(cd/'receipt.json')
assert s['full_physical_pass_cases']==c['full_physical_pass_cases']==12
assert s['original_budget_admitted_cases']==c['original_budget_admitted_cases']==0
rows=[]
for a,b,sa,ca in zip(sp['plans'],cp['plans'],s['rows'],c['rows']):
 assert a['command']==b['command'] and a['target']==b['target'] and a['budget']==b['budget'] and a['source']==b['source'] and a['place']==b['place']
 assert a['seed'] is not None and b['seed'] is None
 assert sa['status']==ca['status']=='FULL_PHYSICAL_ENDPOINT_PASS'
 for x,d in ((a,sd),(b,cd)):
  log=(d/f'w{x["width"]}_m{x["index"]}/run.log').read_text()
  assert ('ROUTECAST_RESUME_LOADED_TREES' in log)==(d==sd)
 rows.append(dict(width=a['width'],index=a['index'],seed_cpd_ns=sa['cpd_ns'],cold_cpd_ns=ca['cpd_ns'],seed_wirelength=sa['wirelength'],cold_wirelength=ca['wirelength'],seed_budget_violations=sa['violation_ids'],cold_budget_violations=ca['violation_ids'],printed_joint_nonregression=F(sa['cpd_ns'])<=F(ca['cpd_ns']) and sa['wirelength']<=ca['wirelength']))
seed=r['arms']['seed']['declared_cohort_seconds'];cold=r['arms']['cold']['declared_cohort_seconds'];bindings[str(Path(__file__))]=sha(Path(__file__))
assert all(sha(f)==h for f,h in bindings.items())
out=dict(bindings=bindings,rows=rows,seed_declared_cohort_seconds=seed,cold_declared_cohort_seconds=cold,observed_seed_over_cold_ratio=seed/cold,observed_time_gain=seed<cold,all_original_budgets_admitted=False,printed_joint_nonregression_cases=sum(x['printed_joint_nonregression'] for x in rows),paired_speedup_proved=False,full_original_input_workflow_seconds=None,scope='Two fresh sequential complete12 declared-boundary observations. Seed includes cold preparation/import/serialization; both include all physical/Fraction audits. Native commands/input bytes identical apart from explicit seed environment. No canonical reload/original HDL equivalence, replicated paired time gain or unseen-family proof.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k not in ('bindings','rows')})
