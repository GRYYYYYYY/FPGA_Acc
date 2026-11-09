"""Full12 owned workflow seed and new native proof parity to frozen independent audits."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/owned_inventory_seed_native_audit_v1_2026-10-08';B=R/'experiments/retained_seed_session_native_cohort_v3_2026-10-08';S=R/'experiments/retained_seed_session_cohort_v3_2026-10-08'
r=json.loads((D/'receipt.json').read_text());b=json.loads((B/'verification.json').read_text());s=json.loads((S/'receipt.json').read_text())
for doc in (r,b,s):assert all(sha(f)==h for f,h in doc['bindings'].items())
assert len(r['rows'])==12 and r['cold_inventory_builds']==3
for x,y,z in zip(r['rows'],b['rows'],s['rows']):
 assert (x['width'],x['index'])==(y['width'],y['index'])==(z['width'],z['index'])
 name=f'w{x["width"]}_m{x["index"]}'
 assert (D/(name+'_seed')/'seed.route').read_bytes()==Path(z['route']).read_bytes()
 assert json.loads((D/(name+'_seed')/'forest.json').read_text())==json.loads(Path(z['route']).with_name('forest.json').read_text())
 assert (D/name/'output.route').read_bytes()==(B/name/'output.route').read_bytes()
 assert json.loads((D/name/'original_budget_verification.json').read_text())==json.loads((B/name/'original_budget_verification.json').read_text())
 assert x['cpd_ns']==y['cpd_ns'] and x['wirelength']==y['wirelength'] and x['violation_ids']==y['violation_ids']
assert sum(sum(x['phases'].values()) for x in r['rows'])<=r['declared_component_seconds']
report=dict(bindings={str(f):sha(f) for f in (D/'receipt.json',B/'verification.json',S/'receipt.json',Path(__file__))},all12_seed_forest_and_native_bytes_full_proofs_equal=True,total_connections=sum(x['connections'] for x in r['rows']),observed_declared_component_seconds=r['declared_component_seconds'],original_budget_admitted_cases=r['original_budget_admitted_cases'],phase_totals={k:sum(x['phases'][k] for x in r['rows']) for k in r['rows'][0]['phases']},scope='Actual12 native runs plus complete seed/forest/native bytes and all physical/budget proofs identical to independently audited frozen v3. External verifier costs excluded from measured component; no matching new cold arm, full original-input workflow gain or canonical pin/HDL equivalence.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
