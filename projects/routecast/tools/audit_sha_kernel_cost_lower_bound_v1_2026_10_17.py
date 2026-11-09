"""Read-only authentication and fixed-other-cost kernel elimination bound."""
import hashlib,json
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'experiments/sha_resident_work_profile_seed_complete_workflow_v1_2026-10-10'
OUT=ROOT/'experiments/sha_kernel_cost_lower_bound_v1_2026-10-17'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
names=['cpu_wall_analysis.json','cost_envelope.json','work_verification.json','verification.json']
docs={n:json.loads((D/n).read_text()) for n in names}
checks=[]
for n,d in docs.items():
 for p,h in d.get('bindings',{}).items():
  q=Path(p);actual=sha(q) if q.is_file() else None
  checks.append(dict(proof=n,path=p,expected=h,actual=actual,passes=actual==h))
assert all(x['passes'] for x in checks), 'Bound source drift: refuse arithmetic promotion'
e=docs['cost_envelope.json']; rows={r['arm']:r for r in e['rows']}
cold=Decimal(rows['cold']['continuous_seconds']);seed=Decimal(rows['seed']['continuous_seconds'])
live=next(r for r in docs['cpu_wall_analysis.json']['rows'] if r['case']=='fresh_live_feedback')
kernel=sum((Decimal(str(p['bidi_wall']))+Decimal(str(p['forward_wall'])) for p in live['phases']),Decimal(0))
assert sum(p['bidi_calls']+p['forward_calls'] for p in live['phases'])==7459
assert docs['work_verification.json']['all7459_per_request_work_count_invariants_pass']
remaining=seed-kernel
assert remaining>cold
out=dict(bindings={str(D/n):sha(D/n) for n in names},source_sha256=sha(__file__),binding_checks=checks,all_current_direct_bindings_pass=True,cold_seconds=str(cold),seed_seconds=str(seed),nested_kernel_seconds=str(kernel),hypothetical_zero_kernel_seed_seconds=str(remaining),minimum_additional_non_kernel_reduction_seconds=str(remaining-cold),driver_threshold_seconds=e['required_handoff_driver_seconds_below_at_fixed_other_costs'],decision='Do not launch another complete workflow on a search-kernel-only acceleration hypothesis. Require a separate measurable reduction of model/transaction/handoff/validation costs or a changed routing utility mechanism.',scope='Single archived SHA1 workflow, fixed-other-cost arithmetic only. Kernel clock is subtracted once, never added to its enclosing driver. No achievable speedup, causal attribution, heldout quality or hardware result is asserted. Independent validation remains mandatory.')
OUT.mkdir(exist_ok=False)
with (OUT/'verification.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['bindings','binding_checks']},indent=2))
