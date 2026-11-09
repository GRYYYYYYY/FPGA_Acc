"""Feasible physical/budget input must remain pending missing canonical/native gates."""
import json,hashlib
from pathlib import Path
from combined_actual_change_review_v1_2026_10_18 import CombinedReview
from unified_rr_audit_inventory_v1 import read
from memoized_fraction_path_delay_unified_v1 import FractionPathMemo
R=Path(__file__).resolve().parents[1];D=R/'experiments/combined_review_pending_gate_v1_2026-10-18';D.mkdir(exist_ok=False)
pp=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json';c=json.loads(pp.read_text())['cases'][0];meta=json.loads(Path(c['old']).read_text());copy=D/'old_endpoints.json'
with copy.open('x') as f:json.dump(meta,f)
graph=Path(meta['inputs']['graph']['path']);inv=read(graph,meta['graph_sha256']);memo=FractionPathMemo(graph,meta['graph_sha256'],inv);review=CombinedReview(copy,graph.with_name('design.route'),inv,memo);answer=review.evaluate(copy,graph.with_name('design.route'),c['budget']);assert not answer['budget']['violation_ids'] and answer['physical_delta']['overflow_units']==0;assert answer['decision']=='PENDING_CANONICAL_AND_NATIVE_ACCEPTANCE' and not answer['accepted']
with copy.open('a') as f:f.write('\n')
try:review.evaluate(copy,graph.with_name('design.route'),c['budget'])
except ValueError as e:assert str(e)=='Stale previous state'
else:raise AssertionError('Changed endpoint metadata accepted')
files=[Path(__file__),R/'tools/combined_actual_change_review_v1_2026_10_18.py',pp,Path(c['old']),Path(c['budget']),graph,graph.with_name('design.route')];bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,budget_and_physical_feasible=True,missing_canonical_native_gate_never_accepted=True,stale_previous_endpoint_rejected=True,scope='No-op old-state pending-gate and private endpoint-copy mutation contract; not a successful placement update.'),f,indent=2);f.write('\n')
print('PASS feasible remains pending; stale prior endpoint rejected')
