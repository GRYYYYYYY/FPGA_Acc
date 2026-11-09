"""Authenticate profile outputs and compare complete model state to frozen runs."""
import json
import pstats
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools'))
from pre_route_endpoints import sha

out = R / 'experiments/aes_workspace_profile_v1_2026-10-08'
bindings = {str(Path(__file__)): sha(Path(__file__))}
rows = []
for name in sys.argv[1:]:
    w = out / name
    ref = R / 'experiments/aes_native_demand_workspace_v1_2026-10-08' / name / 'resident'
    receipts = []
    for root in [w / 'resident', ref]:
        p = root / 'receipt.json'
        d = json.loads(p.read_text())
        assert all(sha(k) == v for k, v in d['bindings'].items())
        assert all(sha(k) == v for k, v in d['files'].items())
        bindings[str(p)] = sha(p)
        receipts.append(d)
    for file in ['initial.json', 'floors.json', 'sketch.json', 'round0.json', 'round1.json']:
        a, b = w / 'resident' / file, ref / file
        assert json.loads(a.read_text()) == json.loads(b.read_text())
        bindings.update({str(a): sha(a), str(b): sha(b)})
    assert len(receipts[0]['rounds']) == len(receipts[1]['rounds']) == 2
    for a, b in zip(receipts[0]['rounds'], receipts[1]['rounds']):
        assert {k: v for k, v in a.items() if k not in ['seconds', 'state_file']} == {k: v for k, v in b.items() if k not in ['seconds', 'state_file']}
    profile = w / 'profile.pstats'
    bindings[str(profile)] = sha(profile)
    stats = pstats.Stats(str(profile))
    functions = []
    for (file, line, function), (primitive, calls, self_seconds, cumulative, callers) in stats.stats.items():
        functions.append(dict(file=file, line=line, function=function, calls=calls,
                              primitive_calls=primitive, self_seconds=self_seconds,
                              cumulative_seconds=cumulative))
    rows.append(dict(name=name, complete_state_and_event_parity=True,
                     instrumented_total_seconds=stats.total_tt,
                     top_self=sorted(functions, key=lambda x: x['self_seconds'], reverse=True)[:30],
                     top_cumulative=sorted(functions, key=lambda x: x['cumulative_seconds'], reverse=True)[:30]))
assert all(sha(k) == v for k, v in bindings.items())
result = dict(bindings=bindings, rows=rows,
              scope='Function-level cProfile diagnosis only. Instrumented times are not ordinary runtime or speedup evidence; previously observed mapped candidates, not heldout validation.')
(out / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
for row in rows:
    print(row['name'], 'PARITY PASS', row['instrumented_total_seconds'])
    for f in row['top_self'][:12]:
        print(f['function'], f['calls'], round(f['self_seconds'], 3), round(f['cumulative_seconds'], 3))
