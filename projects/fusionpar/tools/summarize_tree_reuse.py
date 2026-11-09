#!/usr/bin/env python3
"""Summarize independently audited tree-reuse comparisons without a speedup claim."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import statistics


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def summarize(suites, audits, evidence):
    if len(suites) != len(audits):
        raise ValueError('one independent audit required per suite')
    result = {'schema': 'FUSIONPAR_TREE_REUSE_STATUS_V1',
              'research_status': 'local_development_QoR_improvements_not_independent_fusion_benefit',
              'stable_speedup_claim': False, 'designs': {}, 'totals': {}, 'evidence': [],
              'limitations': ['Development inputs, not held-out validation',
                             'Two repeats test semantic reproducibility, not statistical timing stability',
                             'After a commit, later proposals may differ across modes',
                             'Sequential retained-tree and best placer + PR controls remain required',
                             'No physical FPGA measurements; router timers include CPU scratch/control work']}
    sources = []
    unit_counts = set()
    for suite, audit_path in zip(suites, audits):
        root = suite.resolve()
        a = json.loads((root/'audit.json').read_text())
        audit = json.loads(audit_path.read_text())
        if not audit['pass'] or audit['suite_audit_sha256'] != sha(root/'audit.json'):
            raise ValueError('independent audit binding mismatch')
        if a['deterministic'] is not True or a['tree_control_equivalent_to_pr'] is not True:
            raise ValueError('missing repeat/control equivalence')
        if a['tests']['exit_status'] != 0:
            raise ValueError('suite unit tests failed')
        test_log = root/'build/Testing/Temporary/LastTest.log'
        match = re.search(r'fusionpar_joint_tb: PASS \((\d+) checks', test_log.read_text())
        if not match:
            raise ValueError('unit check count missing from CTest log')
        unit_counts.add(int(match[1]))
        sources.append({s['path']: s['sha256'] for s in a['sources']})
        records = a['records']
        first = next(r for r in records if r['mode'] == 'interleaved_tree_control' and r['repeat'] == 0)
        baseline = json.loads((Path(first['directory'])/'validation_0/validation.json').read_text())
        row = {'repeats': a['repeats'], 'deterministic': a['deterministic'],
               'tree_control_equivalent_to_pr': a['tree_control_equivalent_to_pr'],
               'baseline': {k: baseline[k] for k in ('wirelength', 'cpd_ns')},
               'counts': audit['counts'], 'modes': {}, 'matched_candidates_repeat_0': []}
        for mode in sorted({r['mode'] for r in records}):
            runs = [r for r in records if r['mode'] == mode]
            quality = runs[0]['final_native_quality']
            value = {'runs': len(runs), 'commits': sum(r['summary']['commits'] for r in runs),
                     'aborts': sum(r['summary']['aborts'] for r in runs),
                     'final_qor': {k: quality[k] for k in ('wirelength', 'cpd_ns')},
                     'WL_change_pct': (quality['wirelength']/baseline['wirelength']-1)*100,
                     'CPD_change_pct': (quality['cpd_ns']/baseline['cpd_ns']-1)*100,
                     'kernel_searches_per_run': [sum(e['kernel_searches'] for e in r['event_semantics']) for r in runs],
                     'retained_connections_per_run': [sum(len(e['retained_connections']) for e in r['event_semantics']) for r in runs],
                     'event_statuses_repeat_0': [e['status'] for e in runs[0]['event_semantics']]}
            for key, values in {
                'process_wall_s': [r['process']['wall_ns']/1e9 for r in runs],
                'charged_wall_s': [r['charged_wall_ns']/1e9 for r in runs],
                'routing_s': [r['summary']['routing_ns']/1e9 for r in runs],
                'native_validation_s': [r['summary']['native_ns']/1e9 for r in runs],
            }.items():
                value[key] = values
                value['median_'+key] = statistics.median(values)
            row['modes'][mode] = value
        reused = next(r for r in records if r['mode'] == 'interleaved_tree_reuse' and r['repeat'] == 0)
        for old in first['event_semantics']:
            for new in reused['event_semantics']:
                if (old['before'], old['moves']) == (new['before'], new['moves']):
                    row['matched_candidates_repeat_0'].append({
                        'control_proposal': old['proposal'], 'reuse_proposal': new['proposal'],
                        'before': old['before'], 'moves': old['moves'],
                        'control_kernel_searches': old['kernel_searches'], 'reuse_kernel_searches': new['kernel_searches'],
                        'retained_connections': len(new['retained_connections']),
                        'control_status': old['status'], 'reuse_status': new['status']})
        if a['design'] in result['designs']:
            raise ValueError('duplicate design suite')
        result['designs'][a['design']] = row
        for key, count in audit['counts'].items():
            result['totals'][key] = result['totals'].get(key, 0)+count
        for path in (root/'audit.json', audit_path.resolve(), test_log):
            result['evidence'].append({'path': str(path), 'sha256': sha(path)})
    result['same_source_hashes_across_suites'] = all(s == sources[0] for s in sources)
    if not result['same_source_hashes_across_suites']:
        raise ValueError('comparison suites used different source snapshots')
    if len(unit_counts) != 1:
        raise ValueError('unit counts differ between suites')
    result['unit_checks'] = unit_counts.pop()
    for path in [Path(__file__), *evidence]:
        result['evidence'].append({'path': str(path.resolve()), 'sha256': sha(path)})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suites', nargs='+', type=Path, required=True)
    parser.add_argument('--audits', nargs='+', type=Path, required=True)
    parser.add_argument('--evidence', nargs='*', type=Path, default=[])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.suites, args.audits, args.evidence)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['totals'], indent=2))
