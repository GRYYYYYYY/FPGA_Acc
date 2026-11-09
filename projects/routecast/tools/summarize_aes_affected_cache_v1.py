import json
import sys
from pathlib import Path
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools'))
from pre_route_endpoints import sha
out = R / 'experiments/aes_native_demand_affected_cache_v1_2026-10-08'
bindings = {str(Path(__file__)): sha(Path(__file__))}
for file in ['verification.json', 'source_intervention.json']:
    p = out / file
    d = json.loads(p.read_text())
    assert all(sha(k) == v for k, v in d['bindings'].items())
    bindings[str(p)] = sha(p)
assert all(r['all_paths_floors_budgets_epochs_prices_affected_NETs_events_and_both_ledgers_exact_parity'] for r in json.loads((out / 'verification.json').read_text())['rows'])
rows = []
for root in [R / 'experiments/aes_native_demand_workspace_v1_2026-10-08', out]:
    p = root / 'receipt.json'
    d = json.loads(p.read_text())
    assert all(sha(k) == v for k, v in d['bindings'].items())
    bindings[str(p)] = sha(p)
    for row in d['rows']:
        assert row['exit_code'] == 0
        assert all(sha(k) == v for k, v in row['files'].items())
        r = json.loads((root / row['name'] / 'resident' / 'receipt.json').read_text())
        rows.append(dict(variant='workspace' if root != out else 'affected_cache', name=row['name'],
                         process_wall_seconds=row['estimator_process_wall_seconds'],
                         **{k: r[k] for k in ['total_paid_resident_seconds', 'model_setup_seconds', 'initial_seconds', 'feedback_seconds', 'cpp_search_seconds']}))
result = dict(bindings=bindings, rows=rows, scope='Ordinary single serial runs, with all model states and events exact to independently audited original. No repeated/interleaved statistical speed claim, no new native/fullworkflow or unseen-family validation.')
(out / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(rows, indent=2))
