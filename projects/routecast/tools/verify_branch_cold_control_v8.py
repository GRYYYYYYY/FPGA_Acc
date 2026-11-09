"""Independent original-XML arcs/capacity and complete target endpoint check."""
import json
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit_cached import audit
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_cold_branch_control_v8_2026-10-08'
r=json.loads((D/'receipt.json').read_text());p=json.loads((D/'protocol.json').read_text())
assert sha(D/'protocol.json')==r['protocol_sha256'] and all(sha(f)==h for f,h in p['inputs'].items())
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
target=json.loads(Path(case['target']).read_text());graph=Path(target['inputs']['graph']['path']);route=D/'cold/output.route';log=D/'cold/run.log'
assert r['rows'][0]['exit_code']==0 and sha(route)==r['rows'][0]['route_sha256'] and sha(log)==r['rows'][0]['log_sha256']
text=log.read_text();assert 'Completed routing consistency check successfully.' in text and 'VPR succeeded' in text
proof=audit(graph,route);assert proof['all_printed_branch_arc_switch_and_union_checks_pass'] and proof['overflow_units']==0
observed=Counter((name,path[0][0],path[-1][0]) for name,paths in physical_paths(route).items() for path in paths)
expected=Counter((target['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in target['connections']);assert observed==expected
bindings={str(f):sha(f) for f in (D/'receipt.json',D/'protocol.json',Path(case['target']),graph,route,log,Path(__file__),R/'tools/stream_native_route_audit_cached.py',R/'tools/native_route_ledger_import_compact.py')}
assert all(sha(f)==h for f,h in bindings.items())
(D/'physical_endpoint_verification.json').write_text(json.dumps(dict(bindings=bindings,all_target_connections_physical_endpoint_pass=True,connections=sum(expected.values()),physical=proof,scope='Native FULL producer log and independent original XML arcs/types/unique-NET capacity plus complete named endpoint multiset. No independent canonical packed pin/RC budget/STA proof or end-to-end gain.'),indent=2)+'\n')
print('PASS all',sum(expected.values()),'target connections; capacity overflow 0')
