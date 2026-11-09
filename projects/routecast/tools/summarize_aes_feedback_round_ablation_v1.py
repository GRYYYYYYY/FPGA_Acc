"""Report all feedback states without selecting an operating point."""
import json
import sys
from pathlib import Path
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools'))
from pre_route_endpoints import sha
out = R / 'experiments/aes_feedback_round_ablation_v1_2026-10-08'
bindings = {str(Path(__file__)): sha(Path(__file__))}
for file in ['comparison.json', 'metric_verification.json', 'vector_verification.json', 'methodology_notes.json']:
    p = out / file
    d = json.loads(p.read_text())
    assert all(sha(k) == v for k, v in d.get('bindings', {}).items())
    bindings[str(p)] = sha(p)
assert json.loads((out / 'metric_verification.json').read_text())['metric_vectors_recomputed'] == 22
assert all(r['all_concrete_and_spatial_native_capacity_and_prediction_vectors_exact'] for r in json.loads((out / 'vector_verification.json').read_text())['rows'])
data = json.loads((out / 'comparison.json').read_text())
rows = []
for case in data['rows']:
    name = case['name']
    root = R / 'experiments/aes_native_demand_estimates_v1_2026-10-08' / name / 'resident'
    frames = [json.loads((root / (file + '.json')).read_text()) for file in ['initial', 'round0', 'round1']]
    ledger = [{int(k): v for k, v in frame['ledger'].items()} for frame in frames]
    for file in ['initial.json', 'round0.json', 'round1.json', 'receipt.json']:
        p = root / file
        bindings[str(p)] = sha(p)
    receipt = json.loads((root / 'receipt.json').read_text())
    assert all(sha(k) == v for k, v in receipt['bindings'].items())
    assert all(sha(k) == v for k, v in receipt['files'].items())
    for rounds, method in enumerate(['rc_initial', 'wire_round0', 'wire_shared']):
        completed = len(frames[rounds]['records'])
        assert completed == case['required']
        overflow = frames[0]['overflow_units'] if rounds == 0 else receipt['rounds'][rounds - 1]['overflow_after']
        rows.append(dict(name=name, feedback_rounds=rounds, connections=completed,
                         overflow_units=overflow, positive_owned_resources=len(ledger[rounds]),
                         spatial=case['metrics'][method]['spatial'],
                         concrete=case['metrics'][method]['concrete']))
assert all(sha(k) == v for k, v in bindings.items())
(out / 'summary.json').write_text(json.dumps(dict(bindings=bindings, rows=rows,
    scope='All zero/one/two feedback states of both previously observed mapped candidates retained. Descriptive mechanism evidence, no round selection, native QoR/time inference, legal-route claim or heldout validation. No archived partial timer is reported as full cost.'), indent=2) + '\n')
for row in rows:
    print(row['name'], row['feedback_rounds'], row['overflow_units'],
          {k: row['spatial'][k] for k in ['spearman', 'precision_at_k', 'mae']})
