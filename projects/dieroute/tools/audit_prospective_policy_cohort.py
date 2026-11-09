"""Aggregate terminal, hash-bound prospective reports; never rerun routing."""
import hashlib
import json
from pathlib import Path
import sys


def aggregate(baselines, capacity, output):
    refs = {}
    cache = {}

    def sha(path):
        path = Path(path).resolve()
        stat = path.stat()
        key = (str(path), stat.st_size, stat.st_mtime_ns)
        if key not in cache:
            h = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1048576), b''):
                    h.update(block)
            cache[key] = h.hexdigest()
        refs[str(path)] = cache[key]
        return cache[key]

    def read(path, verify=True):
        sha(path)
        value = json.loads(Path(path).read_text())
        if verify:
            for name, expected in value.get('source_sha256', {}).items():
                assert sha(name) == expected, name
        return value

    baseline = read(baselines / 'independent_audit.json')
    policy = read(baselines / 'candidate_policy.json')
    state = read(capacity / 'manifest.json')
    protocol = read(capacity / 'protocol.json')
    labels = ['apex2_seed' + str(i) for i in range(6, 11)]
    assert protocol['labels'] == labels
    assert state['status'] == 'five_prospective_policy_cases_terminal_require_final_cohort_audit'
    assert [v['label'] for v in state['cases']] == labels
    assert len(baseline['outcomes']) == 5
    by_seed = {v['seed']: v for v in baseline['outcomes']}
    assert set(by_seed) == set(range(6, 11))
    rows = []
    for result in state['cases']:
        label = result['label']
        base = by_seed[int(label.split('seed')[1])]
        assert base['native_legal']
        row = {'label': label, 'terminal_status': result['status'],
               'baseline': base, 'joint_quality_pass': False,
               'stage_costs_ns': {k: v for k, v in result.items() if k.endswith('wall_ns')}}
        snapshot = read(capacity / (label + '_mode_snapshot.json'))
        assert snapshot['label'] == label and snapshot['status'] == result['mode_status']
        row['mode_costs'] = [{k: v for k, v in mode.items()
                              if k in ['mode', 'termination'] or k.endswith('wall_ns')}
                             for mode in snapshot.get('modes', [])]
        if 'final_report' not in result:
            assert result['joint_quality_pass'] is False
            row['classification'] = 'execution_or_audit_outcome_unresolved'
            rows.append(row)
            continue
        report = read(result['final_report'])
        assert report['label'] == label
        status = report['status']
        if status == 'prospective_initial_case_decisions_and_native_provenance_reviewed':
            passed = report['joint_quality_pass']
            metrics = {'wirelength': report['quality']['total_wirelength'],
                       'cpd_ns': report['quality']['critical_path_delay_ns'],
                       'model_crossings': report['crossings']}
            assert passed == all(report['checks'].values())
        elif status == 'prospective_native_mode_acceptance_orders_and_native_wirelength_reviewed':
            passed = report['final_original_baseline_joint_pass']
            leaf = read(report['current_state']['audit'])
            metrics = {k: leaf[k] for k in ['wirelength', 'cpd_ns', 'model_crossings']}
            assert passed == all(leaf['checks'].values())
        else:
            assert status == 'prospective_capacity_fallback_mixture_capacity_and_native_selection_reviewed'
            passed = report['joint_quality_pass']
            metrics = None
            if passed:
                leaf = read(report['selected_native_audit'])
                assert all(leaf['checks'].values())
                metrics = {k: leaf[k] for k in ['wirelength', 'cpd_ns', 'model_crossings']}
            else:
                assert report['selected_native_audit'] is None
        assert passed is result['joint_quality_pass']
        if passed:
            assert metrics['wirelength'] <= base['wirelength']
            assert metrics['cpd_ns'] <= base['cpd_ns']
        row.update(classification='verified_joint_pass' if passed else 'verified_policy_quality_failure',
                   joint_quality_pass=passed, final_metrics=metrics,
                   final_report=result['final_report'])
        rows.append(row)
    sha(Path(__file__))
    report = {'status': 'five_prospective_terminal_reports_aggregated_with_hash_verification',
              'planned': 5, 'retained': len(rows),
              'joint_passes': sum(v['joint_quality_pass'] for v in rows),
              'unresolved': sum(v['classification'] == 'execution_or_audit_outcome_unresolved' for v in rows),
              'rows': rows, 'source_sha256': refs,
              'scope': 'Aggregate of typed stage audits with direct evidence hashes rechecked. Same circuit, five new seeds; baseline-informed repairs. No independent rerun of component auditors, cross-circuit generalization, statistical significance, end-to-end acceleration or physical board claim. Stage costs may overlap and must not be summed as cohort wall time.',
              'research_complete': False}
    with output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    return report


if __name__ == '__main__':
    result = aggregate(*(Path(v).resolve() for v in sys.argv[1:]))
    print(json.dumps({k: result[k] for k in ['status', 'planned', 'joint_passes', 'unresolved']}))
