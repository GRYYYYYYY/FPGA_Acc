"""Certify complete paired request coverage and label-only temporal chains."""
import json
from pathlib import Path
from pre_route_endpoints import sha

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'experiments/prince_paired_cost_state_v1_2026-10-20'


def load(path):
    return json.loads(path.read_text())


def main():
    inputs = load(D / 'frozen_inputs.json')
    manifest = load(D / 'dataset_manifest.json')
    audit = load(D / 'independent_verification_v1.json')
    assert audit['status'] == 'ALL_READY_INPUTS_AND48_POLICY_HORIZON_TARGETS_INDEPENDENTLY_RECONCILED'
    for path, digest in audit['bindings'].items():
        assert sha(path) == digest
    requests = inputs['requests']
    key = lambda row: (row['case'], row['mode'], row['horizon'])
    expected = {(r['case'], m, h) for r in inputs['rows']
                for m in ['native', 'hold_pres', 'hold_acc', 'hold_both'] for h in [1, 2]}
    assert len(requests) == len(expected) == 72
    assert {key(r) for r in requests} == expected
    assert len(manifest['rows']) == 72 and {key(r) for r in manifest['rows']} == expected
    available = {i for i, r in enumerate(requests) if r['status'] == 'READY_PLAN_FROZEN'}
    folds = load(D / 'grouped_folds.json')['folds']
    for fold in folds:
        train, test = fold['train_requests'], fold['test_requests']
        assert len(set(train)) == len(train) and len(set(test)) == len(test)
        assert set(train).isdisjoint(test) and set(train) | set(test) == available
    targets = {key(r): r for r in manifest['rows'] if r['status'] != 'NO_READY_INPUT_UNAVAILABLE'}
    checks = 0
    for row in inputs['rows']:
        if row['status'] == 'NO_READY_EVENT':
            continue
        ready = {r['id']: r['acc_bits'] for r in map(json.loads, Path(row['feature_file']).open())}
        for mode in ['native', 'hold_pres', 'hold_acc', 'hold_both']:
            previous = ready
            for horizon in [1, 2]:
                target = targets[row['case'], mode, horizon]
                records = list(map(json.loads, Path(target['target_file']).open()))
                assert len(records) == len(previous)
                assert {r['id']: r['acc_before_global_bits'] for r in records} == previous
                previous = {r['id']: r['acc_after_global_bits'] for r in records}
                checks += len(records)
    result = dict(status='COMPLETE_REQUEST_FOLDS_AND_LABEL_ONLY_HISTORY_CHAIN_CERTIFIED',
                  requests=72, available_requests=len(available), folds=len(folds),
                  history_word_checks=checks,
                  scope='All horizons use the frozen ready inputs. True h1 history is exclusively a target field for h2, never a replacement inference input. No model fit or quality admission.',
                  bindings={str(p): sha(p) for p in [D / n for n in ['frozen_inputs.json', 'dataset_manifest.json', 'grouped_folds.json', 'independent_verification_v1.json']] + [Path(__file__)]})
    with (D / 'role_and_temporal_certificate_v1.json').open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(result['status'], checks)


if __name__ == '__main__':
    main()
