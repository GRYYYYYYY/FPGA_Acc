#!/usr/bin/env python3
"""Generate a manuscript table only from a completely audited cohort."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_new_cohort import audit
from tileplace_vpr import dump_json, sha256


def prepare(protocol_path, seal, output):
    checked = audit(protocol_path, seal, partial=False)
    protocol = json.loads(protocol_path.read_text())
    root = Path(protocol['output_root'])
    matrix = json.loads((root / 'summary.json').read_text())
    details = {r['design']: r for r in checked['cases']}
    lines = [r'\begin{tabular}{lrrrr}', r'\toprule',
             r'Design & Base (ns) & Final (ns) & $\Delta$CPD & $\Delta$WL \\', r'\midrule']
    for row in matrix['cases']:
        name = row['design'].replace('_', r'\_')
        evidence = details[row['design']]
        if row['status'] == 'pass':
            lines.append(f"{name} & {row['baseline']['cpd_ns']:.5f} & {row['final']['cpd_ns']:.5f} & "
                         f"{evidence['cpd_change_pct']:+.2f}\\% & {evidence['wirelength_change_pct']:+.2f}\\% \\\\")
        else:
            layer = 'baseline' if row['failed_stage'] == 'baseline' else (
                'refinement' if row['failed_stage'].startswith('refinement') else 'input')
            lines.append(name + r' & \multicolumn{4}{c}{' + layer + r' failed} \\')
    if 'successful_subset_geomean_change_pct' in checked:
        means = checked['successful_subset_geomean_change_pct']
        lines.extend([r'\midrule',
                      f"Geo. ({checked['successful_cases']}/{checked['expected_cases']}) & -- & -- & "
                      f"{means['cpd']:+.2f}\\% & {means['wirelength']:+.2f}\\% \\\\"])
    lines.extend([r'\bottomrule', r'\end{tabular}', ''])
    output.mkdir(parents=True, exist_ok=True)
    table = output / 'new_cohort_table.tex'
    table.write_text('\n'.join(lines))
    dump_json(output / 'new_cohort_metadata.json', {
        'schema': 'TILEPLACE_NEW_COHORT_PAPER_TABLE_V1', 'status': 'pass',
        'protocol_sha256': seal, 'summary_sha256': checked['matrix_sha256'],
        'completed_cases': checked['completed_cases'], 'successful_cases': checked['successful_cases'],
        'verified_native_trials': sum(r.get('verified_native_trials', 0) for r in checked['cases']),
        'successful_subset_geomean_change_pct': checked.get('successful_subset_geomean_change_pct'),
        'table_sha256': sha256(table), 'scope': checked['scope']})
    return checked


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.protocol.resolve(), args.sha256, args.output.resolve())
    print(json.dumps({'status': 'pass', 'completed_cases': result['completed_cases']}))
