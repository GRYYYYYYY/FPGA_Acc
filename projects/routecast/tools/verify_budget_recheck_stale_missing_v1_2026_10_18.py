"""Supplemental stale route and missing actual path negative tests."""
import json,hashlib
from pathlib import Path
from actual_change_budget_recheck_v1_2026_10_18 import BudgetRecheck
from unified_rr_audit_inventory_v1 import read
from memoized_fraction_path_delay_unified_v1 import FractionPathMemo
R=Path(__file__).resolve().parents[1];D=R/'experiments/budget_recheck_stale_missing_v1_2026-10-18';D.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=R/'experiments/actual_change_budget_recheck_v1_2026-10-18/verification.json';proof=json.loads(base.read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());bindings={str(base):sha(base),**proof['bindings']}
ref=R/'experiments/retained_seed_session_native_cohort_v3_2026-10-08/verification.json';original=json.loads(ref.read_text());bindings[str(ref)]=sha(ref)
for p,h in proof['bindings'].items():
 if p.endswith('/original_budget_verification.json'):assert original['bindings'][p]==h
cases=json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'];c=cases[0];old=json.loads(Path(c['old']).read_text());target=json.loads(Path(c['target']).read_text());budget=json.loads(Path(c['budget']).read_text());graph=Path(old['inputs']['graph']['path']);memo=FractionPathMemo(graph,old['graph_sha256'],read(graph,old['graph_sha256']))
copy=D/'old.route'
with copy.open('x') as f:f.write(graph.with_name('design.route').read_text())
state=BudgetRecheck(old,copy,memo)
missing=D/'missing.route'
with missing.open('x') as f:f.write('')
try:state.evaluate(target,missing,budget,memo)
except ValueError:missing_rejected=True
else:raise AssertionError('Missing paths accepted')
with copy.open('a') as f:f.write('\n')
try:state.evaluate(target,R/'experiments/retained_seed_session_native_cohort_v3_2026-10-08/w8_m0/output.route',budget,memo)
except ValueError as e:
 assert str(e)=='Stale old route';stale_rejected=True
else:raise AssertionError('Stale old route accepted')
bindings[str(Path(__file__))]=sha(__file__)
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,all12_references_match_original_bound_digests=True,missing_actual_paths_rejected=missing_rejected,modified_old_route_rejected=stale_rejected,scope='Supplemental negative contract tests; only private copied route intentionally modified. No full admission or speed proof.'),f,indent=2);f.write('\n')
print('PASS reference bindings, missing actual paths, stale old route')
