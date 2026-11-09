"""Fixed-model rare-event diagnostics, without refitting or model selection."""
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'experiments/prince_paired_response_prediction_v1_2026-10-20'
S = ROOT / 'experiments/prince_paired_cost_state_v1_2026-10-20'


def load(p):
    return json.loads(p.read_text())


def main():
    audit = load(D / 'independent_verification_v1.json')
    for path, digest in audit['bindings'].items():
        assert sha(path) == digest
    evaluation = load(D / 'evaluation.json')
    requests = load(S / 'frozen_inputs.json')['requests']
    frames = {(r['case'], r['mode'], r['horizon']): r for r in load(S / 'dataset_manifest.json')['rows']}
    scores = []
    reliability = []
    for fold in load(S / 'grouped_folds.json')['folds']:
        model = next(m for m in evaluation['models'] if m['heldout_episode'] == fold['heldout_episode'])
        tables = {}
        for kind in ['pooled', 'stock']:
            table = {}
            for r in model[kind]:
                counts = {int(k): v for k, v in r['counts'].items()}
                table[tuple(r['key'])] = (sum(counts.values()),
                    sum(v for o, v in counts.items() if o > 1),
                    sum((o-1)*v for o, v in counts.items() if o > 1))
            tables[kind] = table
        for i in fold['test_requests']:
            q = requests[i]
            row = frames[q['case'], q['mode'], q['horizon']]
            ready = {r['id']: r for r in map(json.loads, Path(row['input_file']).open())}
            labels = list(map(json.loads, Path(row['target_file']).open()))
            for name in ['persistence', 'policy_horizon_pooled', 'policy_horizon_stock']:
                groups = defaultdict(lambda: [0, 0])
                brier = positive_error = negative_error = expected_excess = 0.0
                positive = actual_excess = 0
                for label in labels:
                    r = ready[label['id']]
                    key = q['mode'], q['horizon']
                    if name == 'persistence':
                        n, hits, excess = 0, 0, 0
                    elif name == 'policy_horizon_stock':
                        n, hits, excess = tables['stock'].get(key + (r['occupancy'], r['acc_bits']), tables['pooled'][key])
                    else:
                        n, hits, excess = tables['pooled'][key]
                    probability = Fraction(hits + int(r['occupancy'] > 1), n+1)
                    mean_excess = Fraction(excess + max(r['occupancy']-1, 0), n+1)
                    event = int(label['occupancy'] > 1)
                    error = (float(probability)-event)**2
                    brier += error
                    if event:
                        positive += 1
                        positive_error += error
                    else:
                        negative_error += error
                    expected_excess += float(mean_excess)
                    actual_excess += label['excess']
                    groups[probability][0] += 1
                    groups[probability][1] += event
                n = len(labels)
                # Exact-probability reliability groups avoid label-chosen bin boundaries.
                rel = sum(count*(float(p)-hits/count)**2 for p,(count,hits) in groups.items())/n
                res = sum(count*(hits/count-positive/n)**2 for count,hits in groups.values())/n
                uncertainty = (positive/n)*(1-positive/n)
                assert abs(brier/n - (rel-res+uncertainty)) < 1e-12
                scores.append(dict(case=q['case'], mode=q['mode'], horizon=q['horizon'], model=name,
                    resources=n, event_rows=positive, event_Brier=brier/n,
                    event_only_Brier=positive_error/positive if positive else None,
                    nonevent_only_Brier=negative_error/(n-positive),
                    predicted_event_total=sum(float(p)*count for p,(count,hits) in groups.items()),
                    predicted_excess_total=expected_excess, actual_excess_total=actual_excess,
                    reliability=rel, resolution=res, uncertainty=uncertainty))
                reliability.extend(dict(case=q['case'], mode=q['mode'], horizon=q['horizon'], model=name,
                    probability=[p.numerator,p.denominator], resources=count, events=hits)
                    for p,(count,hits) in sorted(groups.items()))
    out = dict(status='FIXED_MODEL_EXCESS_EVENT_DIAGNOSTICS_WITH_EXACT_RELIABILITY_GROUPS',
        scores=scores, reliability_groups=reliability,
        scope='Development-only diagnostics of already fitted distributions;no refit,threshold selection or native admission. Resource groups are spatially dependent;reliability decomposition is descriptive,not independent-sample confidence.',
        bindings={str(p):sha(p) for p in [D/'evaluation.json',D/'independent_verification_v1.json',Path(__file__)]})
    with (D/'excess_calibration_v1.json').open('x') as f:
        json.dump(out,f,indent=2);f.write('\n')
    for name in ['persistence','policy_horizon_pooled','policy_horizon_stock']:
        rows = [r for r in scores if r['model']==name]
        print(name, 'Brier',sum(r['event_Brier']*r['resources'] for r in rows)/sum(r['resources'] for r in rows),
              'predicted/actual events',sum(r['predicted_event_total'] for r in rows),sum(r['event_rows'] for r in rows),
              'event-only Brier',sum(r['event_only_Brier']*r['event_rows'] for r in rows)/sum(r['event_rows'] for r in rows))


if __name__ == '__main__':
    main()
