"""Profile unchanged complete native branch audit; instrumented times only."""
import cProfile
import json
import pstats
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from stream_native_route_audit import audit

R = Path(__file__).resolve().parents[1]
D = R / 'experiments/ultraembedded_mmc_actual_old_linear_undo_workflow_v14_2026-10-10'
O = R / 'experiments/mmc_complete_native_physical_profile_v1_2026-10-10'
proof = json.loads((D / 'verification.json').read_text())
assert proof['all_cases_both_complete_arms_authenticated']
bindings = closure([Path(__file__), R / 'tools/stream_native_route_audit.py'])
bindings[str(D / 'verification.json')] = sha(D / 'verification.json')
for path, digest in proof['bindings'].items():
    assert sha(path) == digest, path
    bindings[path] = digest
graph = D / 'seed/rr/mmc/rr_graph.xml'
route = D / 'seed/native/mmc/output.route'
for path in [graph, route]:
    bindings[str(path)] = sha(path)
O.mkdir()
profiler = cProfile.Profile()
start = time.perf_counter()
result = profiler.runcall(audit, graph, route)
seconds = time.perf_counter() - start
assert result['all_printed_branch_arc_switch_and_union_checks_pass']
assert result['overflow_units'] == 0 and len(result['connections']) == 115572
assert all(sha(path) == digest for path, digest in bindings.items())
profiler.dump_stats(str(O / 'audit.prof'))
with (O / 'profile.txt').open('w') as stream:
    pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats('cumulative').print_stats(40)
    pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats('tottime').print_stats(40)
(O / 'physical_result.json').write_text(json.dumps(result, separators=(',', ':')) + '\n')
out = dict(bindings=bindings, complete_original_native_branch_audit_pass=True,
           instrumented_seconds=seconds, connections=len(result['connections']),
           physical_edge_count=result['physical_edge_count'],
           files={str(p): sha(p) for p in O.iterdir() if p.is_file()},
           scope='All printed native branches and full original RR XML scanned. Profiling overhead included; cumulative timings overlap. No pin legality, new router performance, heldout, hardware or audit omission claim.')
(O / 'verification.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: v for k, v in out.items() if k not in ['bindings', 'files']}, indent=2))
