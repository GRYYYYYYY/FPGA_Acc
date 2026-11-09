#!/usr/bin/env python3
"""Summarize audited timing-weight outcomes and non-overlapping adapter costs."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

from audit_development import require
from run_development import sha


def summarize(study_path):
    study = json.loads(study_path.read_text())
    phases, counts = defaultdict(int), defaultdict(int)
    profiles = 0
    native_ns = host_ns = 0
    rows = []
    for suite in study['suites']:
        for entry in suite['sources']:
            require(sha(entry['path']) == entry['sha256'], 'changed study evidence')
        receipt_path = Path(suite['sources'][0]['path'])
        receipt = json.loads(receipt_path.read_text())
        require(suite['independent_audit']['pass'] and
                suite['independent_audit']['suite_audit_sha256'] == sha(receipt_path), 'unbound audit')
        for key, value in suite['independent_audit']['counts'].items():
            counts[key] += value
        for record in receipt['records']:
            native_ns += record['summary']['native_ns']
            host_ns += record['process']['wall_ns']
            for p in Path(record['directory']).glob('validation_*/costs.json'):
                require(sha(p) == receipt['artifacts'][str(p.relative_to(receipt_path.parent))], 'cost ledger changed')
                c = json.loads(p.read_text())
                require(c['complete'] and sum(e['wall_ns'] for e in c['phases']) == c['total_ns'], 'incomplete cost ledger')
                profiles += 1
                for e in c['phases']:
                    phases[e['phase']] += e['wall_ns']
        for mode, data in suite['modes'].items():
            samples = data['samples']
            rows.append({'design': suite['design'], 'arm': suite['arm'], 'weight_q8': suite['weight_q8'],
                'mode': mode, 'repeats':len(samples), 'quality':samples[0]['quality'],
                'completed_runs':sum(s['completed'] for s in samples),
                'eligible_runs':sum(s['within_original_2pct_gate'] for s in samples),
                'commits_per_repeat':[s['commits'] for s in samples],
                'median_host_seconds':data['median_host_seconds'],
                'median_charged_seconds':data['median_charged_seconds'],
                'median_phase_seconds':data['median_phase_seconds'],
                'equal_to_old_zero_weight':data['state_events_timing_equal_to_old_weight_zero']})
    total_ns = sum(phases.values())
    require(0 < total_ns <= native_ns <= host_ns, 'nested cost accounting inconsistent')
    return {'schema':'FUSIONPAR_TREE_TIMING_COST_RESULTS_V1',
            'study':{'path':str(study_path.resolve()),'sha256':sha(study_path)},
            'summarizer':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},
            'references':study['references'], 'counts':dict(counts), 'rows':rows,
            'validation_profiles':profiles,
            'costs':{'profiled_body_seconds':total_ns/1e9,'host_native_interval_seconds':native_ns/1e9,
                     'host_total_seconds':host_ns/1e9,
                     'phase_seconds':{k:v/1e9 for k,v in phases.items()},
                     'phase_fraction_of_profiled_body':{k:v/total_ns for k,v in phases.items()},
                     'scope':'Aggregate all 54 development runs; fractions are of profiled adapter bodies, not whole P&R or FPGA time'},
            'limits':study['limits'] + ['No per-design winning-weight selection; default remains zero pending broader evidence',
                  'TP native-routed outputs remain available references; failed full rerouting is not forced into their cost']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('study',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('output already exists')
    result=summarize(args.study.resolve())
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'counts':result['counts'],'validation_profiles':result['validation_profiles'],
                      'costs':result['costs']},indent=2))
