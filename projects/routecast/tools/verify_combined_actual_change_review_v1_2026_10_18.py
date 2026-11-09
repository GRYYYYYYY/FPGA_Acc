"""All12 fail-closed composed reviews against existing full Fraction proofs."""
import json,hashlib,time
from pathlib import Path
from combined_actual_change_review_v1_2026_10_18 import CombinedReview
from unified_rr_audit_inventory_v1 import read
from memoized_fraction_path_delay_unified_v1 import FractionPathMemo
R=Path(__file__).resolve().parents[1];D=R/'experiments/combined_actual_change_review_v1_2026-10-18';D.mkdir(exist_ok=False);bindings={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 p=Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
cases=load(R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json')['cases'];reference=load(R/'experiments/retained_seed_session_native_cohort_v3_2026-10-08/verification.json');rows=[];start=time.perf_counter()
for width in (8,16,32):
 cs=[c for c in cases if c['width']==width];meta=load(cs[0]['old']);graph=Path(meta['inputs']['graph']['path']);inv=read(graph,meta['graph_sha256']);memo=FractionPathMemo(graph,meta['graph_sha256'],inv);tick=time.perf_counter();review=CombinedReview(cs[0]['old'],graph.with_name('design.route'),inv,memo);setup=time.perf_counter()-tick
 for c in cs:
  w,i=c['width'],c['index'];out=R/f'experiments/retained_seed_session_native_cohort_v3_2026-10-08/w{w}_m{i}';ref=load(out/'original_budget_verification.json');assert bindings[str(out/'original_budget_verification.json')]==reference['bindings'][str(out/'original_budget_verification.json')]
  tick=time.perf_counter();answer=review.evaluate(c['target'],out/'output.route',c['budget']);elapsed=time.perf_counter()-tick
  assert answer['budget']['rows']==ref['rows'];assert answer['physical_delta']['node_occupancy']==ref['physical']['node_occupancy'];assert answer['decision']=='REJECT_ORIGINAL_BUDGET' and not answer['accepted'];assert answer['canonical_gate']=='MISSING_NOT_EVALUATED'
  bindings.update(answer['inputs_sha256']);rows.append(dict(width=w,index=i,violations=len(answer['budget']['violation_ids']),decision=answer['decision'],accepted=answer['accepted'],canonical_gate=answer['canonical_gate'],setup_seconds=setup if i==0 else 0,review_seconds=elapsed))
  with (D/f'w{w}_m{i}.json').open('x') as f:json.dump(answer,f,indent=2);f.write('\n')
  print(w,i,answer['decision'],flush=True)
 for e in meta['inputs'].values():bindings[e['path']]=e['sha256']
 bindings[str(graph.with_name('design.route'))]=sha(graph.with_name('design.route'))
for n in ['combined_actual_change_review_v1_2026_10_18.py','verify_combined_actual_change_review_v1_2026_10_18.py','actual_change_budget_recheck_v1_2026_10_18.py','actual_change_physical_delta_v1_2026_10_18.py','stream_native_route_audit_unified_v1.py']:
 p=R/'tools'/n;bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,all12_budget_and_occupancy_match=True,all12_rejected=True,canonical_missing_never_accepted=True,component_seconds=time.perf_counter()-start,scope='Fresh composed diagnostics including full printed audit; canonical/native acceptance not run, no complete workflow or speed gain. Old-state inventory construction excluded from setup subclock but included in outer component.'),f,indent=2);f.write('\n')
