"""Exact descriptive stock-cell dispersion; no fitted forecast or admission."""
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha

D = Path(__file__).resolve().parents[1] / 'experiments/prince_paired_cost_state_v1_2026-10-20'


def load(p):
    return json.loads(p.read_text())


def ratio(x):
    return [x.numerator, x.denominator]


def main():
    certificate = load(D / 'role_and_temporal_certificate_v1.json')
    for p, digest in certificate['bindings'].items():
        assert sha(p) == digest
    manifest = load(D / 'dataset_manifest.json')
    frames, cells, summaries = {}, [], []
    for row in manifest['rows']:
        if row['status'] == 'NO_READY_INPUT_UNAVAILABLE':
            continue
        assert sha(row['input_file']) == row['input_sha256']
        assert sha(row['target_file']) == row['target_sha256']
        ready = {r['id']: r for r in map(json.loads, Path(row['input_file']).open())}
        target = {r['id']: r for r in map(json.loads, Path(row['target_file']).open())}
        assert set(ready) == set(target)
        frames[row['case'], row['mode'], row['horizon']] = target
        groups = defaultdict(Counter)
        for node, r in target.items():
            stock = ready[node]
            assert stock['capacity'] == 1
            groups[stock['occupancy'], stock['acc_bits']][r['occupancy']] += 1
        total_gap = Fraction(0)
        mixed = 0
        for (occ, acc), counts in sorted(groups.items()):
            n = sum(counts.values())
            mean = Fraction(sum(o * count for o, count in counts.items()), n)
            positive = Fraction(sum(count for o, count in counts.items() if o > 0), n)
            excess = Fraction(sum(max(o - 1, 0) * count for o, count in counts.items()), n)
            assert excess == mean - positive
            gap = excess - max(mean - 1, 0)
            assert gap >= 0
            total_gap += n * gap
            mixed += n if len(counts) > 1 else 0
            cells.append(dict(case=row['case'], mode=row['mode'], horizon=row['horizon'],
                              ready_occupancy=occ, ready_acc_bits=acc, resources=n,
                              occupancy_histogram=dict(counts), mean_occupancy=ratio(mean),
                              positive_probability=ratio(positive), expected_excess=ratio(excess),
                              mean_hinge_underestimate=ratio(gap)))
        summaries.append(dict(case=row['case'], mode=row['mode'], horizon=row['horizon'],
                              cells=len(groups), resources=len(target),
                              resources_in_nondeterministic_stock_cells=mixed,
                              aggregate_mean_hinge_underestimate=ratio(total_gap)))
    contrasts = []
    for case in sorted({k[0] for k in frames}):
        for h in [1, 2]:
            native = frames[case, 'native', h]
            for mode in ['hold_pres', 'hold_acc', 'hold_both']:
                other = frames[case, mode, h]
                changes = sum(native[n]['occupancy'] != other[n]['occupancy'] for n in native)
                distance = sum(abs(native[n]['occupancy'] - other[n]['occupancy']) for n in native)
                if h == 1 and mode == 'hold_acc':
                    assert changes == distance == 0
                contrasts.append(dict(case=case, mode=mode, horizon=h,
                                      occupancy_changed_resources=changes, occupancy_l1=distance))
    out = dict(status='EXACT_DESCRIPTIVE_STOCK_CELL_AND_POLICY_CONTRAST_ANALYSIS',
               frames=len(summaries), cells=cells, summaries=summaries, contrasts=contrasts,
               scope='Empirical spatial populations grouped by exact ready occupancy/history within each case,policy,horizon. Mixed cells and Jensen gaps establish limitations of this coarse grouping only;not stochastic uncertainty conditional on full state,forecast error,query cost,or native benefit. No label-tuned bins or fitted model.',
               bindings={str(p): sha(p) for p in [D / 'dataset_manifest.json', D / 'role_and_temporal_certificate_v1.json', Path(__file__)]})
    with (D / 'stock_cell_dispersion_v1.json').open('x') as f:
        json.dump(out, f, indent=2)
        f.write('\n')
    print('frames', len(summaries), 'cells', len(cells), 'positive_gap_frames',
          sum(r['aggregate_mean_hinge_underestimate'][0] > 0 for r in summaries))
    for h in [1, 2]:
        for mode in ['hold_pres', 'hold_acc', 'hold_both']:
            values = [r['occupancy_changed_resources'] for r in contrasts if r['horizon'] == h and r['mode'] == mode]
            print(h, mode, values)


if __name__ == '__main__':
    main()
