"""Post-admission complete online state comparison, no success-only NET selection."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
bindings=closure([Path(__file__)])
def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
def admit(p,key):
 r=load(p);assert r[key]
 for field in ('bindings','files'):
  for f,h in r.get(field,{}).items():assert sha(f)==h;bindings[f]=h
 return r
N=R/'experiments/mmc_actual_old_joint_fallback_linear_v11_2026-10-09'
T=R/'experiments/mmc_triangular_span_v9_2026-10-09'
L=R/'experiments/ultraembedded_mmc_continuous_workflow_v10_2026-10-09'
new=admit(N/'verification.json','complete_online_feedback_physical_and_actual_old_fallback_events_pass')
admit(T/'verification.json','complete_candidate_physical_and_events_pass')
admit(L/'verification.json','all_cases_both_complete_arms_authenticated')
models=[('linear',L/'seed/model/mmc'),('triangular',T/'model'),('actual_old_linear_fallback',N/'model')]
rows=[];initials=[]
for name,m in models:
 initial=load(m/'initial.json');initials.append(initial);receipt=load(m/'receipt.json');final=load(m/'sketch.json');protocol=load(m/'protocol.json')
 assert final['completed_connections']==final['required_connections']==115572 and protocol['rounds']==2
 rounds=[]
 for rr in receipt['rounds']:
  events=rr['events'];committed=sum(e['status']=='COMMITTED' for e in events)
  fallbacks=[e['fallback'] for e in events if 'fallback' in e]
  rounds.append(dict(round=rr['round_index'],affected_NETs=len(events),committed=committed,retained=len(events)-committed,fallback_calls=len(fallbacks),fallback_accepted=sum(f['status']=='ACCEPT_STRICT_IMPROVEMENT' for f in fallbacks),overflow_before=rr['overflow_before'],overflow_after=rr['overflow_after']))
 rows.append(dict(method=name,completed=115572,rounds=rounds,final_overflow_units=final['overflow_units'],fallback_seconds=receipt.get('fallback_seconds',0),scope='Current model outcome; overuse is demand, not a legal joint route.'))
assert initials[0]==initials[1]==initials[2]
assert sum(x['fallback_calls'] for x in rows[-1]['rounds'])==new['fallback_calls']
assert sum(x['fallback_accepted'] for x in rows[-1]['rounds'])==new['fallback_accepted']
assert all(sha(p)==h for p,h in bindings.items())
D=R/'experiments/mmc_linear_fallback_online_comparison_v1_2026-10-09';D.mkdir(exist_ok=False)
r=dict(bindings=bindings,full_initial_inputs_floors_budgets_and_ledger_identical=True,rows=rows,candidate_model_and_complete_validation_seconds=new['continuous_model_and_complete_validation_seconds'],scope='Descriptive authenticated same-design online trajectories. Affected schedule evolves independently, not paired NET causal attribution. Model/audit time excludes conversion/native/QoR; not complete workflow gain or strict heldout.')
(D/'comparison.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(rows,indent=2))
