"""Positive-control witness admission, never independent timing-target admission."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from required_node_budget_preflight_v1 import EvidenceMismatch
def batch_preflight(path,expected_digest,requests):
 path=Path(path)
 if sha(path)!=expected_digest:raise EvidenceMismatch('verification changed')
 report=json.loads(path.read_text());bindings=dict(report['bindings']);rp=path.parent/'receipt.json'
 if str(rp) not in bindings:raise EvidenceMismatch('unbound receipt')
 receipt=json.loads(rp.read_text());bindings.update(receipt['bindings'])
 if not all(sha(p)==h for p,h in bindings.items()):raise EvidenceMismatch('witness authority changed')
 plans={p['step']:p for p in receipt['plans']};proofs={p['step']:p for p in report['rows']};seen=set();rows=[]
 for q in requests:
  step=q['step']
  if step in seen or step not in plans:raise EvidenceMismatch('unknown or duplicate step')
  seen.add(step);plan=plans[step];proof=proofs[step]
  for key in ('endpoints','budgets','state','witness_route'):
   if Path(q[key]).resolve()!=Path(plan[key]).resolve() or sha(q[key])!=bindings.get(plan[key]):raise EvidenceMismatch('request differs from witness')
  if not proof['known_joint_model_feasible'] or not proof['all_original_arc_fraction_budget_parent_capacity_pass']:raise EvidenceMismatch('witness not verified')
  rows.append(dict(step=step,decision='ADMIT_KNOWN_FEASIBLE_MODEL_POSITIVE_CONTROL',scope='Legal-witness equality fixture only; not original model budgets or independent STA/userclock targets.'))
 if sha(path)!=expected_digest or not all(sha(p)==h for p,h in bindings.items()):raise EvidenceMismatch('witness changed during batch')
 return rows
