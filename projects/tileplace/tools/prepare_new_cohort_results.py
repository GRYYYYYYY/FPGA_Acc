#!/usr/bin/env python3
"""Render all cohort cases only after a complete independent artifact audit."""
import argparse
import json
from pathlib import Path

from audit_new_cohort import audit
from tileplace_vpr import dump_json, sha256


def render(protocol_path, seal):
    checked = audit(protocol_path, seal, partial=False)
    protocol = json.loads(protocol_path.read_text())
    root = Path(protocol['output_root'])
    matrix = json.loads((root / 'summary.json').read_text())
    lines = ['# Prospective TilePlace local cohort', '',
             f"Completed {checked['completed_cases']}/{checked['expected_cases']} cases; "
             f"{checked['successful_cases']} successful paired evaluations.", '',
             'All failures remain in the cohort denominator. No retries, seed/width/weight adaptation, '
             'or architecture changes were permitted.', '',
             '| Design | Status | Baseline CPD (ns) | Final CPD (ns) | CPD change | '
             'Wirelength change | Exact repeats | End-to-end seconds |',
             '|---|---|---:|---:|---:|---:|---:|---:|']
    details = {r['design']: r for r in checked['cases']}
    for row in matrix['cases']:
        evidence = details[row['design']]
        if row['status'] == 'pass':
            lines.append(f"| {row['design']} | pass | {row['baseline']['cpd_ns']:.5f} | "
                         f"{row['final']['cpd_ns']:.5f} | {evidence['cpd_change_pct']:+.3f}% | "
                         f"{evidence['wirelength_change_pct']:+.3f}% | {len(row['repeats'])} | "
                         f"{row['end_to_end_s']:.2f} |")
        else:
            reason = row['error'].replace('|', '\\|').replace('\n', ' ')
            lines.append(f"| {row['design']} | failed: {reason} | — | — | — | — | "
                         f"{len(row['repeats'])} retained | {row['end_to_end_s']:.2f} |")
    if 'successful_subset_geomean_change_pct' in checked:
        means = checked['successful_subset_geomean_change_pct']
        lines.extend(['', f"Successful-subset geometric means: CPD {means['cpd']:+.3f}%; "
                      f"wirelength {means['wirelength']:+.3f}%. These exclude failed cases; "
                      'the success count above defines the denominator.'])
    lines.extend(['', 'End-to-end seconds include native baseline, CPU input generation, proxy timing, '
                  'contract packing, both refinement repetitions and controller validation. They are '
                  'not a single-run speedup or physical FPGA measurement.', '',
                  'Initial static timing uses proxy path edge delays; final CPD and wirelength come '
                  'from native VPR. This local logic-oriented cohort does not establish architecture '
                  'generalization or strict historical blindness.', '',
                  f'Protocol SHA-256: `{seal}`.',
                  f"Implementation SHA-256: `{protocol['implementation_sha256']}`.",
                  f"Summary SHA-256: `{sha256(root / 'summary.json')}`.", ''])
    return checked, '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--audit-output', type=Path, required=True)
    args = parser.parse_args()
    result, text = render(args.protocol.resolve(), args.sha256)
    with args.output.open('x') as stream:
        stream.write(text)
    dump_json(args.audit_output, result)
    print(json.dumps({'status': 'pass', 'cases': result['completed_cases'],
                      'successful_cases': result['successful_cases']}))
