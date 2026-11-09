"""Whole-episode heldout auxiliary phase-response prediction."""
import json
from pathlib import Path
from collections import defaultdict, Counter
from pre_route_endpoints import sha

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'experiments/prince_paired_response_prediction_v1_2026-10-20'


def load(p):
    return json.loads(p.read_text())


def main():
    protocol = load(D / 'protocol.json')
    for p, digest in protocol['bindings'].items():
        assert sha(p) == digest
    source = ROOT / protocol['source']
    inputs = load(source / 'frozen_inputs.json')
    manifest = load(source / 'dataset_manifest.json')
    requests = inputs['requests']
    rows = { (r['case'], r['mode'], r['horizon']): r for r in manifest['rows'] }
    data = {}
    for i, request in enumerate(requests):
        if request['status'] != 'READY_PLAN_FROZEN':
            continue
        row = rows[request['case'], request['mode'], request['horizon']]
        assert sha(row['target_file']) == row['target_sha256']
        assert sha(row['input_file']) == row['input_sha256']
        ready = {r['id']: r for r in map(json.loads, Path(row['input_file']).open())}
        data[i] = [(ready[t['id']]['occupancy'], ready[t['id']]['acc_bits'], t['occupancy'])
                   for t in map(json.loads, Path(row['target_file']).open())]
    scores, models = [], []
    for fold in load(source / 'grouped_folds.json')['folds']:
        pooled, stock = defaultdict(Counter), defaultdict(Counter)
        for i in fold['train_requests']:
            q = requests[i]
            key = q['mode'], q['horizon']
            for occ, acc, target in data[i]:
                pooled[key][target] += 1
                stock[key + (occ, acc)][target] += 1
        models.append(dict(heldout_episode=fold['heldout_episode'],train_requests=fold['train_requests'],
                           pooled=[dict(key=list(k),counts=dict(v)) for k,v in pooled.items()],
                           stock=[dict(key=list(k),counts=dict(v)) for k,v in stock.items()]))
        for i in fold['test_requests']:
            q = requests[i]
            key = q['mode'], q['horizon']
            for model in protocol['models']:
                mse = brier = excess_mse = bias = rare = 0.0
                rare_n = fallback = 0
                for occ, acc, target in data[i]:
                    if model == 'persistence':
                        counts = Counter()
                    elif model == 'policy_horizon_pooled':
                        counts = pooled[key]
                    else:
                        counts = stock.get(key + (occ, acc), pooled[key])
                        fallback += key + (occ, acc) not in stock
                    n = sum(counts.values()) + 1
                    mean = (sum(o*c for o,c in counts.items()) + occ) / n
                    positive = (sum(c for o,c in counts.items() if o>0) + int(occ>0)) / n
                    excess = (sum(max(o-1,0)*c for o,c in counts.items()) + max(occ-1,0)) / n
                    assert abs(excess - (mean-positive)) < 1e-12
                    truth = max(target-1,0)
                    mse += (mean-target)**2
                    brier += (positive-int(target>0))**2
                    excess_mse += (excess-truth)**2
                    bias += excess-truth
                    if truth:
                        rare += (excess-truth)**2
                        rare_n += 1
                n = len(data[i])
                scores.append(dict(case=q['case'],mode=q['mode'],horizon=q['horizon'],model=model,
                                   heldout_episode=fold['heldout_episode'],resources=n,occupancy_MSE=mse/n,
                                   positive_Brier=brier/n,excess_MSE=excess_mse/n,aggregate_excess_bias=bias,
                                   excess_target_rows=rare_n,excess_target_only_MSE=rare/rare_n if rare_n else None,
                                   pooled_fallback_resources=fallback))
    assert len(scores) == 144
    output = dict(status='GROUPED_DEVELOPMENT_PREDICTIONS_SCORED_PENDING_INDEPENDENT_AUDIT',
                  scores=scores,models=models,unavailable_requests=24,original_full9_gate=False,
                  bindings={str(p):sha(p) for p in [D/'protocol.json',Path(__file__)]})
    with (D/'evaluation.json').open('x') as f:
        json.dump(output,f,indent=2);f.write('\n')
    for model in protocol['models'][1:]:
        for metric in ['occupancy_MSE','positive_Brier','excess_MSE']:
            wins=0
            for s in scores:
                if s['model'] != model: continue
                baseline=next(t for t in scores if t['case']==s['case'] and t['mode']==s['mode'] and t['horizon']==s['horizon'] and t['model']=='persistence')
                wins += s[metric] < baseline[metric]-1e-12
            print(model,metric,'strict wins vs persistence',wins,'/48')


if __name__ == '__main__':
    main()
