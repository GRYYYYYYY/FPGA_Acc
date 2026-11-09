#!/usr/bin/env python3
"""Compare fresh TP nine-closure quality with archived FP nine-evaluation results."""
import argparse
import json
from pathlib import Path
from statistics import median

from audit_development import require
from run_development import ROOT, sha
from run_tp_budget_reference import binding, checked


def summarize(path):
    study = json.loads(path.read_text())
    require(study['pass'], 'TP study did not pass')
    for entry in study['bindings']:
        checked(entry)
    fp_path = ROOT / 'experiments/feedback_budget_status_2026-10-13.json'
    fp = json.loads(fp_path.read_text())
    designs = {}
    for design, data in study['designs'].items():
        rows = data['runs']
        require(len(rows) == 5 and data['deterministic'] and all(r['closure_calls'] == 9 for r in rows),
                'incomplete TP repeats or budget')
        for row in rows:
            checked(row['report'])
            checked(row['process'])
        for entry in fp['designs'][design]['evidence']:
            checked(entry)
        receipt_path = next(checked(e) for e in fp['designs'][design]['evidence'] if Path(e['path']).name == 'audit.json')
        receipt = json.loads(receipt_path.read_text())
        require(receipt['deterministic'] and receipt['feedback_evaluation_budget_matched'] and receipt['attempts'] == 9,
                'FP budget not matched')
        manifest_path = receipt_path.parent / 'bundle/manifest.json'
        require(sha(manifest_path) == receipt['artifacts']['bundle/manifest.json'], 'FP manifest changed')
        manifest = json.loads(manifest_path.read_text())
        initial = rows[0]['population'][0]['artifacts']
        for kind in ('net', 'place', 'route'):
            require(initial[kind]['sha256'] == manifest['inputs'][kind]['sha256'], 'TP/FP initial state differs')
            checked(initial[kind])
        quality = lambda r: {k: r[k] for k in ('wirelength', 'cpd_ns')}
        selected = rows[0]['selected']
        fp_modes = {}
        for mode, mode_data in fp['designs'][design]['modes'].items():
            runs = [r for r in receipt['records'] if r['mode'] == mode]
            require(len(runs) == 5 and all(r['summary']['evaluations'] == 9 for r in runs), 'FP incomplete evaluations')
            require(all(quality(r['final_native_quality']) == mode_data['quality'] for r in runs), 'FP quality differs')
            fq = mode_data['quality']
            fp_modes[mode] = {'quality': fq, 'median_host_seconds': mode_data['median_host_seconds'],
                             'median_charged_seconds': mode_data['median_charged_seconds'],
                             'FP_better_final_lexicographic': (fq['wirelength'], fq['cpd_ns']) <
                                                            (selected['wirelength'], selected['cpd_ns'])}
        designs[design] = {'TP_selected_trial': selected['trial'], 'TP_selected_quality': quality(selected),
                           'TP_selected_accepted_online': selected['tp_accepted'],
                           'TP_eligible_trials': sum(r['eligible'] for r in rows[0]['population'][1:]),
                           'TP_legal_trials': sum(r['legal'] for r in rows[0]['population'][1:]),
                           'TP_reported_final_quality': quality(rows[0]['TP_final']),
                           'TP_wall_samples_seconds': [r['wall_seconds'] for r in rows],
                           'TP_median_wall_seconds': median(r['wall_seconds'] for r in rows),
                           'TP_trajectory_semantics_sha256': rows[0]['semantics_sha256'],
                           'FP_modes': fp_modes}
    return {'schema': 'FUSIONPAR_TP_NINE_CLOSURE_REFERENCE_RESULTS_V1',
            'study': binding(path), 'FP_reference': binding(fp_path), 'summarizer': binding(Path(__file__)),
            'counts': {'TP_runs': 15, 'TP_candidate_evaluations': 135, 'FP_reference_runs': 30,
                       'FP_reference_candidate_evaluations': 270},
            'designs': designs, 'limits': study['limits']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('study', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists')
    result = summarize(args.study.resolve())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['designs'], indent=2))
