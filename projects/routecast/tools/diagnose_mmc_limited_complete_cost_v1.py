"""Authenticated full cost budget diagnostic; never authorizes audit omission."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
D=R/'experiments/ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10'
bindings={str(Path(__file__)):sha(Path(__file__))}
def load(p):
 d=json.loads(p.read_text())
 for section in ['bindings','files']:
  for k,v in d.get(section,{}).items():assert sha(k)==v;bindings[k]=v
 bindings[str(p)]=sha(p);return d
v=load(D/'verification.json');assert v['all_cases_both_complete_arms_authenticated']
c=load(D/'stage_cost_verification_v13.json');assert c['stage_accounting_pass']
s=next(x for x in c['rows'] if x['arm']=='seed')
model=next(x['seconds'] for x in s['stages'] if x.get('log','').endswith('mmc_model_native_seed.log'))
audit=next(x['seconds'] for x in s['stages'] if x.get('log','').endswith('mmc_shared_audits.log'))
remaining=s['total_seconds']-model-audit
out=dict(bindings=bindings,cold_seconds=v['cold_continuous_cohort_seconds'],seed_seconds=s['total_seconds'],model_handoff_seconds=model,complete_model_audits_seconds=audit,remaining_complete_seed_seconds=remaining,conditional_model_plus_audits_budget_seconds=v['cold_continuous_cohort_seconds']-remaining,time_gate=v['observed_single_trial_continuous_time_gain'],joint_gate=v['observed_single_trial_joint_time_and_printed_native_qor_gate'],scope='Arithmetic assuming all other measured seed costs fixed. All model/audit costs remain mandatory. Not feasibility, omission permission, causal optimization estimate, stability, heldout or silicon evidence.')
assert all(sha(k)==h for k,h in bindings.items())
(D/'cost_budget_diagnostic_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
