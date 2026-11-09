"""Single full audit comparison; original reference retained, no default change."""
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from stream_native_route_audit import audit as control
from stream_native_route_audit_expat_v2 import audit as candidate

R = Path(__file__).resolve().parents[1]
D = R / 'experiments/ultraembedded_mmc_actual_old_linear_undo_workflow_v14_2026-10-10'
P = R / 'experiments/mmc_complete_native_physical_profile_v1_2026-10-10'
O = R / 'experiments/mmc_complete_native_expat_reverse_v2_2026-10-10'
proof = json.loads((P / 'verification.json').read_text())
assert proof['complete_original_native_branch_audit_pass']
bindings = closure([Path(__file__), R / 'tools/stream_native_route_audit.py', R / 'tools/stream_native_route_audit_expat_v2.py'])
for section in ['bindings', 'files']:
    for path, digest in proof[section].items():
        assert sha(path) == digest, path
        bindings[path] = digest
bindings[str(P / 'verification.json')] = sha(P / 'verification.json')
contract_path = R / 'experiments/native_expat_contract_v2_2026-10-10/verification.json'
contract = json.loads(contract_path.read_text())
assert contract['all_selected_contracts_match_original']
assert all(sha(k) == h for k,h in contract['bindings'].items())
bindings.update(contract['bindings'])
bindings[str(contract_path)] = sha(contract_path)
O.mkdir()
reference = json.loads((P / 'physical_result.json').read_text())
graph = D / 'seed/rr/mmc/rr_graph.xml'
route = D / 'seed/native/mmc/output.route'
rows = []
for name, function in [('candidate', candidate), ('control', control)]:
    start = time.perf_counter()
    result = function(graph, route)
    seconds = time.perf_counter() - start
    assert result == reference, name
    rows.append(dict(arm=name, seconds=seconds, full_result_equal=True))
    (O / 'rows.json').write_text(json.dumps(rows, indent=2) + '\n')
    print(rows[-1], flush=True)
assert all(sha(path) == digest for path, digest in bindings.items())
out = dict(bindings=bindings, complete_original_result_equal=True, rows=rows,
           candidate_over_control=rows[0]['seconds']/rows[1]['seconds'],
           scope='Single candidate-first local comparison of namespace-corrected v2. Complete original route/branch/arc/switch/unique-NET/capacity output equal, full XML scanned. No malformed XML contract, pin legality, stable speedup, full workflow or heldout claim; default unchanged.')
(O / 'verification.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k:v for k,v in out.items() if k!='bindings'}, indent=2))
