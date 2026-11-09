"""Stage accounting under authenticated complete arm clocks; no omitted audits."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha1_actual_old_linear_expat_workflow_v1_2026-10-10'
p=D/'verification.json';v=json.loads(p.read_text());assert v['all_cases_both_complete_arms_authenticated']
assert all(sha(k)==h for k,h in v['bindings'].items())
sp=D/'stages.json';stages=json.loads(sp.read_text());rp=D/'rows.json';rows=json.loads(rp.read_text());current=None;groups={x['arm']:[] for x in rows}
for s in stages:
 if 'log' in s:
  path=Path(s['log']);current=path.relative_to(D).parts[0];assert current in groups and s['exit_code']==0
 else:assert s['arm']==current and s['stage']=='canonical_reload_complete'
 groups[current].append(s)
result={}
for row in rows:
 arm=row['arm'];xs=groups[arm];total=row['continuous_arm_seconds'];summed=sum(x['seconds'] for x in xs);assert 0<summed<=total
 result[arm]=dict(continuous_seconds=total,observed_stage_seconds=summed,unassigned_in_arm_seconds=total-summed,stages=xs)
seed=groups['seed'];model=next(s['seconds'] for s in seed if s.get('log','').endswith('_model_native_seed.log'));audit=next(s['seconds'] for s in seed if s.get('log','').endswith('_shared_audits.log'))
c=v['cold_continuous_cohort_seconds'];s=v['seed_continuous_cohort_seconds'];rest=s-model-audit
out=dict(bindings={**v['bindings'],str(p):sha(p),str(sp):sha(sp),str(rp):sha(rp),str(Path(__file__)):sha(Path(__file__))},arms=result,model_handoff_seconds=model,complete_model_audit_seconds=audit,seed_other_complete_cost_seconds=rest,conditional_model_plus_audit_budget_for_gain_seconds=c-rest,seed_over_cold_ratio=s/c,qor=v['cases'],scope='Single sequential observed workflow stage accounting, residual includes uninstrumented hashing/copies/inventory/control costs. Conditional budget arithmetic holds other costs fixed and does not authorize removing audits; no stable causal performance, true timing, heldout or hardware claim.')
assert all(sha(k)==h for k,h in out['bindings'].items())
(D/'cost_diagnosis_v1.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:x for k,x in out.items() if k not in ['bindings','arms']},indent=2))
