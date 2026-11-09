#!/usr/bin/env python3
"""Summarize fully audited equal-evaluation-budget feedback experiments."""
import argparse
import json
from pathlib import Path
from statistics import median

from audit_development import require, semantic_digest
from run_development import ROOT, sha
from validate_candidate import read_state


def binding(path):
    return {'path': str(path.resolve()), 'sha256': sha(path)}


def trajectory(record):
    run = Path(record['directory'])
    quality = {}
    for path in run.glob('validation_*/validation.json'):
        q = json.loads(path.read_text())
        require(q['candidate_sha256'] == sha(path.parent/'candidate.state'), 'candidate binding changed')
        quality[semantic_digest(read_state(path.parent/'candidate.state'))] = {
            k: q[k] for k in ('wirelength', 'cpd_ns')}
    initial = json.loads((run/'validation_0/validation.json').read_text())
    current = {k: initial[k] for k in ('wirelength', 'cpd_ns')}
    rows = [{'evaluation': 0, 'quality': current}]
    for i, e in enumerate(record['event_semantics'], 1):
        if e['status'] == 'committed':
            current = quality[e['candidate_digest']]
        rows.append({'evaluation': i, 'quality': current, 'phase': e['phase'],
                     'status': e['status'], 'proposal': e['proposal'],
                     'kernel_searches': e['kernel_searches'], 'expanded': e['expanded']})
    require(current == {k: record['final_native_quality'][k] for k in current}, 'trajectory final quality differs')
    return rows


def summarize(work, audits):
    result = {'schema': 'FUSIONPAR_FEEDBACK_BUDGET_RESULTS_V1', 'designs': {}, 'counts': {},
              'protocol': binding(ROOT/'experiments/feedback_budget_protocol_2026-10-13.json'),
              'limits': ['Equal evaluated-candidate count, not equal search work or elapsed time',
                         'All three designs are development cases; no held-out generalization',
                         'Five semantic repetitions are not independent random design samples',
                         'All failures, feedback generation, native checking and timing work are charged',
                         'Per-evaluation trajectories are descriptive, not a tuned stopping policy',
                         'No RC predictor, physical FPGA results or universal fusion speedup claim']}
    for design in ('ex5p', 'alu4', 'misex3'):
        suite = work / (design + '_feedback_budget_v1')
        receipt_path = suite/'audit.json'
        r = json.loads(receipt_path.read_text())
        audit_path = audits/(design+'_feedback_budget_audit_2026-10-13.json')
        a = json.loads(audit_path.read_text())
        require(a['pass'] and a['suite_audit_sha256'] == sha(receipt_path), 'missing/bad independent audit')
        require(r['repeats'] == 5 and r['attempts'] == 9 and r['deterministic'] and
                r['feedback_evaluation_budget_matched'] and len(r['records']) == 10, 'budget/repeat mismatch')
        modes = {}
        for mode in ('interleaved_tree_reuse', 'interleaved_tree_feedback'):
            records = [x for x in r['records'] if x['mode'] == mode]
            require(len(records) == 5 and {x['repeat'] for x in records} == set(range(5)), 'missing repeats')
            first = next(x for x in records if x['repeat'] == 0)
            samples = []
            for x in records:
                events = x['event_semantics']
                require(len(events) == x['summary']['evaluation_budget'] == x['summary']['evaluations'] == 9,
                        'not a matched nine-evaluation sample')
                require(x['final_state_sha256'] == first['final_state_sha256'] and
                        events == first['event_semantics'] and x['timing_events'] == first['timing_events'],
                        'semantic determinism flag disagrees with records')
                samples.append({'repeat': x['repeat'], 'host_seconds': x['process']['wall_ns']/1e9,
                    'charged_seconds': x['charged_wall_ns']/1e9, 'commits': x['summary']['commits'],
                    'native_adapter_seconds': x['summary']['native_ns']/1e9,
                    'routing_seconds': x['summary']['routing_ns']/1e9,
                    'aborts': x['summary']['aborts'], 'repairs': x['summary']['placement_repairs'],
                    'repair_commits': sum(e['phase']=='placement_repair' and e['status']=='committed' for e in events),
                    'kernel_searches': sum(e['kernel_searches'] for e in events),
                    'expanded': sum(e['expanded'] for e in events)})
            modes[mode] = {'quality': {k: first['final_native_quality'][k] for k in ('wirelength', 'cpd_ns')},
                           'samples': samples, 'median_host_seconds': median(x['host_seconds'] for x in samples),
                           'median_native_adapter_seconds': median(x['native_adapter_seconds'] for x in samples),
                           'median_routing_seconds': median(x['routing_seconds'] for x in samples),
                           'median_charged_seconds': median(x['charged_seconds'] for x in samples),
                           'trajectory_repeat0': trajectory(first), 'final_state_sha256': first['final_state_sha256']}
        result['designs'][design] = {'modes': modes, 'audit': a,
            'evidence': [binding(receipt_path), binding(audit_path)]}
        for key, value in a['counts'].items():
            result['counts'][key] = result['counts'].get(key, 0) + value
    result['summarizer'] = binding(Path(__file__))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-root', type=Path, default=ROOT/'work')
    parser.add_argument('--audit-root', type=Path, default=ROOT/'experiments')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists')
    result = summarize(args.work_root.resolve(), args.audit_root.resolve())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'counts': result['counts'], 'designs': {
        d: {m: {k: x[k] for k in ('quality', 'median_host_seconds')} for m, x in v['modes'].items()}
        for d, v in result['designs'].items()}}, indent=2))
