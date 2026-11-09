"""Classify original-budget transitions using authenticated archived audits."""
import json,hashlib
from pathlib import Path
from fractions import Fraction as F
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_budget_transition_v1_2026-10-18';D.mkdir(exist_ok=False)
bindings={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 p=Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
prior=load(R/'experiments/previous_native_budget_origin_v1_2026-10-18/verification.json')
native=load(R/'experiments/retained_seed_session_native_cohort_v3_2026-10-08/verification.json')
for report in [prior,native]:
 for p,h in report['bindings'].items():
  assert sha(p)==h,p
  bindings[p]=h
cases=load(R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json')['cases']
rows=[]
for case in cases:
 width,index=case['width'],case['index'];old=load(case['old']);target=load(case['target'])
 a={q['connection_id']:q for q in old['connections']};b={q['connection_id']:q for q in target['connections']}
 direct={cid for cid in a if (a[cid]['source'],a[cid]['sink'])!=(b[cid]['source'],b[cid]['sink'])}
 nets={b[cid]['net_id'] for cid in direct};closure={cid for cid in b if b[cid]['net_id'] in nets}
 before={x['connection_id']:x for x in next(x for x in prior['rows'] if x['width']==width)['old_state_budget_violations']}
 after=load(R/f'experiments/retained_seed_session_native_cohort_v3_2026-10-08/w{width}_m{index}/original_budget_verification.json')
 nr=next(x for x in native['rows'] if (x['width'],x['index'])==(width,index))
 violations={x['connection_id'] for x in after['rows'] if not x['budget_pass']}
 assert violations==set(nr['violation_ids'])==set(after['violation_ids'])
 details=[]
 for cid in sorted(set(before)|violations):
  q=next(x for x in after['rows'] if x['connection_id']==cid)
  excess=F(q['delay_seconds'])*10**9-F(q['budget_ns'])
  assert (excess>0)==(cid in violations)
  details.append(dict(connection_id=cid,transition='persistent' if cid in before and cid in violations else 'resolved' if cid in before else 'new',endpoint_changed=cid in direct,dirty_net=cid in closure,after_excess_ns=str(excess),before_excess_ns=str(F(before[cid]['delay_ns'])-F(before[cid]['budget_ns'])) if cid in before else None))
 rows.append(dict(width=width,index=index,before=len(before),after=len(violations),persistent=sorted(set(before)&violations),resolved=sorted(set(before)-violations),new=sorted(violations-set(before)),new_outside_dirty_net=sorted((violations-set(before))-closure),details=details))
 print(width,index,'persistent',len(set(before)&violations),'resolved',len(set(before)-violations),'new',len(violations-set(before)),'new outside dirty NET',len((violations-set(before))-closure),flush=True)
bindings[str(Path(__file__))]=sha(__file__)
report=dict(bindings=bindings,rows=rows,all_bound_inputs_current=True,scope='Fresh set and exact rational excess accounting over authenticated historical original-XML/Fraction audits; not a new native run or a new independent physical replay. Persistent means same violating connection, not identical path or violation magnitude. Dirty-NET membership does not prove causal responsibility.',decision='Every target has newly violating connections, including w8/w16 whose initial states were budget-feasible. Initial w32 violations alone do not explain failure. Do not silently relax budgets or promote this seed strategy as complete accepted incrementality.')
with (D/'verification.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
