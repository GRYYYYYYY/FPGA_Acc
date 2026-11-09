#!/usr/bin/env python3
"""Summarize the complete frozen cohort, retaining every coverage failure."""
import argparse
import json
from pathlib import Path
from statistics import median
from audit_development import require
from run_development import ROOT, sha


def binding(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def checked(entry):
    path = Path(entry['path'])
    require(sha(path) == entry['sha256'], 'changed evidence: ' + str(path))
    return path


def summarize(path):
    study = json.loads(path.read_text())
    protocol = json.loads(checked(study['protocol']).read_text())
    freeze_path = checked(study['freeze'])
    freeze = json.loads(freeze_path.read_text())
    for entry in freeze['inputs']:
        checked(entry)
    # Original source files may acquire later development changes. The evidence
    # is the archived frozen byte copy, plus each suite's completion assertion.
    for entry in freeze['sources']:
        original = Path(entry['path'])
        snapshot = path.parent / 'sources' / original.relative_to(ROOT.parent)
        require(sha(snapshot) == entry['sha256'], 'frozen source archive changed')
    designs = {d: {'tracks': {}} for d in protocol['designs']}
    for design, data in designs.items():
        baseline_path = (ROOT / protocol['input_root'] / design / 'baseline/baseline.json').resolve()
        baseline = json.loads(baseline_path.read_text())
        data['initial_quality'] = {k: baseline[k] for k in ('wirelength', 'cpd_ns')}
        data['initial_baseline'] = binding(baseline_path)
    counts = {'selected_designs': len(designs), 'expected_suites': 12,
              'audited_suites': 0, 'failed_suites': 0, 'completed_host_runs': 0,
              'qor_commits': 0, 'aborts': 0, 'timing_barriers': 0, 'placement_repairs': 0}
    seen = set()
    for row in study['rows']:
        key = (row['design'], row['track'])
        require(key not in seen and row['design'] in designs, 'duplicate/unknown cohort row')
        seen.add(key)
        directory = Path(row['directory'])
        process_prefix = directory.parent / (row['track'] + '_process')
        for stream in ('stdout', 'stderr'):
            require(sha(process_prefix.with_suffix('.' + stream + '.log')) == row['process'][stream + '_sha256'],
                    'changed outer process log')
        track = {'completed': row['completed'], 'audited': row['audited'],
                 'outer_seconds': row['process']['wall_ns'] / 1e9,
                 'process': binding(process_prefix.with_suffix('.process.json'))}
        designs[row['design']]['tracks'][row['track']] = track
        if not row['completed'] or not row['audited']:
            counts['failed_suites'] += 1
            failures = []
            for p in sorted(directory.glob('*.process.json')):
                process = json.loads(p.read_text())
                if process['exit_status']:
                    stderr = p.with_name(p.name.replace('.process.json', '.stderr.log'))
                    failures.append({'receipt': binding(p), 'exit_status': process['exit_status'],
                                     'stderr': binding(stderr), 'stderr_tail': stderr.read_text()[-3500:]})
            track['failures'] = failures
            track['completed_host_processes_before_failure'] = len(list(directory.glob('process_*.process.json')))
            if row.get('audit_failure'):
                track['audit_failure'] = row['audit_failure']
            continue
        publication_path = checked(row['publication_audit'])
        publication = json.loads(publication_path.read_text())
        require(publication['pass'], 'publication audit failed')
        receipt_path = directory / 'audit.json'
        require(sha(receipt_path) == publication['suite_audit_sha256'], 'suite receipt changed')
        receipt = json.loads(receipt_path.read_text())
        require(receipt['deterministic'] and receipt['repeats'] == 5 and
                receipt['rr_export_backend'] == 'xml' and receipt['route_tree_timing_weight_q'] == 0,
                'wrong frozen policy or nondeterministic suite')
        expected = next(t for t in protocol['tracks'] if t['id'] == row['track'])
        require(receipt['attempts'] == expected['attempts'], 'wrong proposal/evaluation limit')
        require(len(receipt['records']) == 10, 'incomplete mode/repeat population')
        require({(r['mode'], r['repeat']) for r in receipt['records']} ==
                {(m, i) for m in expected['modes'] for i in range(5)}, 'mode/repeat identity mismatch')
        counts['audited_suites'] += 1
        counts['completed_host_runs'] += 10
        for key in ('qor_commits', 'aborts', 'timing_barriers', 'placement_repairs'):
            counts[key] += publication['counts'][key]
        track['evidence'] = [binding(receipt_path), binding(publication_path)]
        track['modes'] = {}
        track['equal_evaluation_budget_matched'] = receipt['feedback_evaluation_budget_matched'] if row['track'] == 'equal_evaluation_feedback' else None
        track['configuration_seconds'] = json.loads((directory / 'configure.process.json').read_text())['wall_ns'] / 1e9
        track['build_seconds'] = json.loads((directory / 'build_command.process.json').read_text())['wall_ns'] / 1e9
        track['tests_seconds'] = json.loads((directory / 'tests.process.json').read_text())['wall_ns'] / 1e9
        track['conversion_seconds'] = json.loads((directory / 'prepare.process.json').read_text())['wall_ns'] / 1e9
        for mode in expected['modes']:
            runs = [r for r in receipt['records'] if r['mode'] == mode]
            samples = []
            quality = {k: runs[0]['final_native_quality'][k] for k in ('wirelength', 'cpd_ns')}
            for r in runs:
                require(all(r['final_native_quality'][k] == value for k, value in quality.items()), 'repeat QoR differs')
                events = r['event_semantics']
                committed = [e for e in events if e['status'] == 'committed']
                s = r['summary']
                other_ns = r['process']['wall_ns'] - s['native_ns'] - s['routing_ns']
                require(other_ns >= 0, 'native/router clocks exceed enclosing process time')
                samples.append({'repeat': r['repeat'], 'host_seconds': r['process']['wall_ns'] / 1e9,
                                'charged_seconds': r['charged_wall_ns'] / 1e9,
                                'native_adapter_seconds': s['native_ns'] / 1e9,
                                'other_host_seconds': other_ns / 1e9,
                                'routing_seconds': s['routing_ns'] / 1e9,
                                'evaluations': s['evaluations'], 'commits': s['commits'], 'aborts': s['aborts'],
                                'repair_attempts': s['placement_repairs'],
                                'attempted_instance_moves': sum(len(e['moves']) for e in events),
                                'committed_instance_moves': sum(len(e['moves']) for e in committed),
                                'unique_committed_instances': len({m[0] for e in committed for m in e['moves']}),
                                'kernel_searches': sum(e['kernel_searches'] for e in events),
                                'expanded_nodes': sum(e['expanded'] for e in events)})
            track['modes'][mode] = {'quality': quality, 'samples': samples,
                                   'median_host_seconds': median(r['host_seconds'] for r in samples),
                                   'median_charged_seconds': median(r['charged_seconds'] for r in samples),
                                   'median_other_host_seconds': median(r['other_host_seconds'] for r in samples),
                                   'median_native_adapter_seconds': median(r['native_adapter_seconds'] for r in samples),
                                   'median_routing_seconds': median(r['routing_seconds'] for r in samples),
                                   'state_sha256': runs[0]['final_state_sha256']}
        names = expected['modes']
        a, b = (track['modes'][m]['quality'] for m in names)
        qa, qb = (a['wirelength'], a['cpd_ns']), (b['wirelength'], b['cpd_ns'])
        track['final_lexicographic_comparison'] = 'same' if qa == qb else names[0] if qa < qb else names[1]
    require(len(seen) == 12, 'missing cohort suite rows')
    counts['fully_audited_designs'] = sum(len(d['tracks']) == 2 and all(t['audited'] for t in d['tracks'].values())
                                         for d in designs.values())
    return {'schema': 'FUSIONPAR_INDEPENDENT_VALIDATION_RESULTS_V1', 'study': binding(path),
            'summarizer': binding(Path(__file__)), 'counts': counts, 'designs': designs,
            'limits': study['limits'] + ['Five repeats test determinism, not five independent designs',
                       'other_host_seconds subtracts disjoint host native-adapter and router intervals from enclosing host process; residual includes loading, proposal generation, snapshots, accounting, other validation and bookkeeping; not pure proposal time',
                       'native_adapter_seconds is the host interval including candidate state serialization, Python startup and full adapter subprocess; not VPR-only execution time',
                       'prepare/validation timers overlap nested routing/native work and are not added to the disjoint cost decomposition',
                       'Failed suite partial host processes are retained separately and do not count as a completed five-repeat comparison']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('study', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        p.error('output already exists')
    result = summarize(a.study.resolve())
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['counts'], indent=2))
