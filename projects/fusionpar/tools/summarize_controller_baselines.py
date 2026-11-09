#!/usr/bin/env python3
"""Re-audit staged retention and frozen TP/PR archives, then summarize all runs."""
import argparse
import json
from pathlib import Path
from statistics import median

from audit_development import audit, require
from run_development import ROOT, sha


def connection_priorities(path):
    tokens = iter(path.read_text().split())
    require(next(tokens) == 'FUSIONPAR_TEXT_V1', 'wrong design schema')
    def number():
        return int(next(tokens))
    def skip(n):
        for _ in range(n):
            number()
    for _ in range(number()):
        skip(4)
        skip(3 * number())
    for _ in range(number()):
        skip(2)
        skip(number())
        skip(2)
    for _ in range(number()):
        skip(1)
        skip(4 * number())
    priorities = []
    for _ in range(number()):
        skip(6)
        priorities.append(number())
        skip(4)
        skip(number())
    require(not list(tokens), 'trailing design data')
    return priorities


def binding(path):
    return {'path': str(path.resolve()), 'sha256': sha(path)}


def summarize(work):
    result = {'schema': 'FUSIONPAR_CONTROLLER_BASELINES_V1', 'designs': {},
              'staged_counts': {}, 'fixed_placement_PR_counts': {},
              'limits': ['Three development designs; no held-out evaluation',
                         'Equal primary budgets do not imply equal evaluated moves or compute',
                         'One reproduced TP run per design, then five PR runs, not five full pipelines',
                         'TP and FP objectives and budgets differ; no speedup ratio',
                         'Native-legal PR outputs outside the common QoR gate are ineligible',
                         'CPU/C-model only; no physical FPGA results']}
    for design in ('ex5p', 'alu4', 'misex3'):
        staged = work / (design + '_sequential_retained_v1')
        pipeline = work / (design + '_frozen_tp_pr_v2')
        a = json.loads((staged / 'audit.json').read_text())
        p = json.loads((pipeline / 'pipeline.json').read_text())
        audits = {'staged': audit(staged), 'pipeline': audit(pipeline / 'routing')}
        for relative, digest in p['artifacts'].items():
            require(sha(pipeline / relative) == digest, 'pipeline archive changed: ' + relative)
        for path, digest in p['placer_artifacts'].items():
            require(sha(path) == digest, 'placer archive changed: ' + path)
        for entry in p['pipeline_inputs']:
            require(sha(entry['path']) == entry['sha256'], 'pipeline input changed')
        require(p['publication_audit']['suite_audit_sha256'] == audits['pipeline']['suite_audit_sha256'],
                'pipeline receipt is bound to another suite')
        require(a['repeats'] == 5 and len(a['records']) == 15 and a['deterministic'] and
                a['retained_sequential_shared_equivalent'], 'staged repeats/control mismatch')
        manifest = json.loads((pipeline / 'routing/bundle/manifest.json').read_text())
        reference = json.loads((staged / 'bundle/manifest.json').read_text())
        require(manifest['inputs']['net']['sha256'] == reference['inputs']['net']['sha256'],
                'packed netlist changed')
        ref = {(c['net'], c['net_pin_index']): c for c in reference['connections']}
        target = {(c['net'], c['net_pin_index']): c for c in manifest['connections']}
        require(len(ref) == len(reference['connections']) and len(target) == len(manifest['connections']) and
                ref.keys() == target.keys(), 'connection identity coverage mismatch')
        priorities = connection_priorities(pipeline / 'routing/bundle/design.txt')
        require(priorities == [c['priority'] for c in manifest['connections']], 'encoded priority mismatch')
        for key, c in target.items():
            require(c['priority'] == ref[key].get('priority', ref[key]['id']) and
                    all(c[k] == ref[key][k] for k in ('net_name', 'source_instance', 'sink_instance')),
                    'PR ordering or endpoint instance identity changed')
        modes = {}
        for mode in sorted({r['mode'] for r in a['records']}):
            records = [r for r in a['records'] if r['mode'] == mode]
            require(len(records) == 5, 'missing staged repeat')
            modes[mode] = {'repeats': 5,
                'quality': {k: records[0]['final_native_quality'][k] for k in ('wirelength', 'cpd_ns')},
                'commits_per_repeat': [r['summary']['commits'] for r in records],
                'aborts_per_repeat': [r['summary']['aborts'] for r in records],
                'host_seconds': [r['process']['wall_ns']/1e9 for r in records],
                'median_host_seconds': median(r['process']['wall_ns'] for r in records)/1e9,
                'median_charged_seconds': median(r['charged_wall_ns'] for r in records)/1e9,
                'final_state_sha256': records[0]['final_state_sha256']}
        require(len(p['rows']) == 5 and p['PR_deterministic'], 'missing/nondeterministic PR repeats')
        result['designs'][design] = {'modes': modes, 'audits': audits,
            'priority_alignment': {'connections': len(priorities), 'encoded_priorities_verified': True,
                                   'different_from_trace_index': sum(i != v for i, v in enumerate(priorities))},
            'pipeline': {k: p[k] for k in ('placer_quality', 'placer_closures', 'placer_repeats', 'PR_repeats',
                        'placer_matches_historical_final_place', 'placer_reused_from_this_session', 'rows')},
            'median_charged_TP_PR_seconds': median(r['charged_placer_plus_PR_wall_ns'] for r in p['rows'])/1e9,
            'eligible_PR_repeats': sum(r['within_original_2pct_gate'] for r in p['rows']),
            'evidence': [binding(staged/'audit.json'), binding(pipeline/'pipeline.json')]}
        for key, which in (('staged_counts', 'staged'), ('fixed_placement_PR_counts', 'pipeline')):
            for counter, value in audits[which]['counts'].items():
                result[key][counter] = result[key].get(counter, 0) + value
    result['summarizer'] = binding(Path(__file__))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-root', type=Path, default=ROOT/'work')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists')
    result = summarize(args.work_root.resolve())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('staged_counts', 'fixed_placement_PR_counts')}))
