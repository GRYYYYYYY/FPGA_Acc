"""Full top-20 truth rank diagnostics; no fitting or operating-point selection."""
import json
import sys
from pathlib import Path
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools'))
from pre_route_endpoints import sha
out = R / 'experiments/aes_feedback_round_ablation_v1_2026-10-08'
proof = out / 'vector_verification.json'
d = json.loads(proof.read_text())
assert all(sha(k) == v for k, v in d['bindings'].items())
bindings = {str(proof): sha(proof), str(Path(__file__)): sha(Path(__file__))}
rows = []
for name in ['aes_cipher', 'aes_inv_cipher']:
    p = out / name / 'comparison_vectors.json'
    bindings[str(p)] = sha(p)
    bins = json.loads(p.read_text())['bins']
    truth_order = sorted(bins, key=lambda b: (-b['native'] / b['capacity'], b['key']))
    truth_top = truth_order[:20]
    assert len(truth_top) == 20
    methods = {}
    for method in ['rc_initial', 'wire_round0', 'wire_shared']:
        ordered = sorted(bins, key=lambda b: (-b['predictions'][method] / b['capacity'], b['key']))
        ranks = {tuple(b['key']): i + 1 for i, b in enumerate(ordered)}
        entries = []
        for tr, b in enumerate(truth_top, 1):
            value = b['predictions'][method] / b['capacity']
            greater = sum(x['predictions'][method] / x['capacity'] > value for x in bins)
            equal = sum(x['predictions'][method] / x['capacity'] == value for x in bins)
            rank = ranks[tuple(b['key'])]
            assert greater + 1 <= rank <= greater + equal
            entries.append(dict(key=b['key'], truth_rank=tr, prediction_rank=rank,
                                prediction_tie_rank_interval=[greater + 1, greater + equal],
                                native_utilization=b['native'] / b['capacity'],
                                prediction_utilization=value, capacity=b['capacity']))
        methods[method] = dict(truth_top20=entries, top20_hits=sum(x['prediction_rank'] <= 20 for x in entries),
                               missed_even_under_best_tie_order=sum(x['prediction_tie_rank_interval'][0] > 20 for x in entries))
    rows.append(dict(name=name, methods=methods))
assert all(sha(k) == v for k, v in bindings.items())
(out / 'hotspot_rank_diagnosis.json').write_text(json.dumps(dict(bindings=bindings, rows=rows,
    scope='Descriptive ranks of all true top20 spatial bins on known frozen native labels. Ties explicitly bounded. No parameter tuning, label-trained model, native QoR inference or unseen-family claim.'), indent=2) + '\n')
for row in rows:
    print(row['name'], {m: {k: v[k] for k in ['top20_hits', 'missed_even_under_best_tie_order']} for m, v in row['methods'].items()})
