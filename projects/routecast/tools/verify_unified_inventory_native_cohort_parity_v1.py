"""Full12 proof parity and explicit inventory-epoch rejection."""
import json
from pathlib import Path
from dataclasses import replace
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v1 import read
from stream_native_route_audit_unified_v1 import audit
R=Path(__file__).resolve().parents[1]
D=R/'experiments/unified_inventory_native_cohort_audit_v1_2026-10-08'
B=R/'experiments/memoized_fraction_native_cohort_audit_v1_2026-10-08'
v=json.loads((D/'verification.json').read_text());b=json.loads((B/'verification.json').read_text())
for doc in (v,b):assert all(sha(f)==h for f,h in doc['bindings'].items())
assert v['rows']==b['rows'] and v['memo_stats']==b['memo_stats'] and len(v['rows'])==12
bindings={str(D/'verification.json'):sha(D/'verification.json'),str(B/'verification.json'):sha(B/'verification.json')}
for row in v['rows']:
 name=f'w{row["width"]}_m{row["index"]}_original_budget_verification.json'
 assert json.loads((D/name).read_text())==json.loads((B/name).read_text())
 bindings[str(B/name)]=sha(B/name)
n=R/'experiments/retained_seed_session_native_cohort_v2_2026-10-08'
p=json.loads((n/'protocol.json').read_text())['plans'][0]
t=json.loads(Path(p['target']).read_text());g=Path(t['inputs']['graph']['path'])
inv=read(g,t['graph_sha256'])
try:audit(g,n/'w8_m0/output.route',replace(inv,digest='0'*64))
except ValueError as e:assert 'Wrong inventory epoch' in str(e)
else:raise AssertionError('Wrong epoch accepted')
for name in ('verify_unified_inventory_native_cohort_parity_v1.py','verify_unified_inventory_native_cohort_audit_v1.py','unified_rr_audit_inventory_v1.py','stream_native_route_audit_unified_v1.py','memoized_fraction_path_delay_unified_v1.py','native_route_audit_cache.py','path_rc.py','pre_route_endpoints.py','native_route_ledger_import_compact.py','audit_native_route.py'):
 f=R/'tools'/name;bindings[str(f)]=sha(f)
report=dict(bindings=bindings,all12_full_rows_and_physical_proofs_equal=True,total_connections=sum(r['connections'] for r in v['rows']),wrong_inventory_epoch_rejected=True,observed_unified_audit_seconds=v['audit_component_seconds'],reference_memo_audit_seconds=b['audit_component_seconds'],scope='All12 archived native routes, complete physical proofs and original exact budget rows identical. Single sequential audit observations, no paired runtime gain, new native run, canonical pin/HDL or heldout validation. Explicit owned inventory assumes construction via authenticated reader, not untrusted forged Inventory objects.')
(D/'parity_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
