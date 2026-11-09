"""Full archive parity and profile accounting, without inferring causal speedup."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
D=R/'experiments/memoized_fraction_audit_cost_profile_v1_2026-10-08'
B=R/'experiments/memoized_fraction_native_cohort_audit_v1_2026-10-08'
v=json.loads((D/'verification.json').read_text())
b=json.loads((B/'verification.json').read_text())
for doc in (v,b):
 assert all(sha(p)==h for p,h in doc['bindings'].items())
assert v['rows']==b['rows'] and v['memo_stats']==b['memo_stats']
assert len(v['phase_rows'])==12
for row,phase in zip(v['rows'],v['phase_rows']):
 assert (row['width'],row['index'])==(phase['width'],phase['index'])
 f=f'w{row["width"]}_m{row["index"]}_original_budget_verification.json'
 assert json.loads((D/f).read_text())==json.loads((B/f).read_text())
for key,total in v['phase_totals'].items():
 assert total==sum(row[key] for row in v['phase_rows']) and total>=0
subtotal=sum(v['phase_totals'].values())
assert subtotal<=v['audit_component_seconds']
report=dict(bindings={str(p):sha(p) for p in (D/'verification.json',B/'verification.json',Path(__file__),R/'tools/memoized_fraction_path_delay_v1.py')},all12_full_proofs_equal=True,total_connections=sum(r['connections'] for r in v['rows']),phase_totals=v['phase_totals'],audit_component_seconds=v['audit_component_seconds'],unallocated_seconds=v['audit_component_seconds']-subtotal,scope='Sequential wall-clock partition of one full12 archive audit. Exact row and physical proof parity with frozen memo baseline; no repeated paired comparison, native rerun or gain claim. Physical parser cache remains shared within this process. Initial binding checks before audit clock excluded; final closure checks inside clock included as unallocated.')
(D/'cost_profile_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
