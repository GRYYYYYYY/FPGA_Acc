"""Extract design timing and constraint coverage without granting signoff."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    data = args.report.read_bytes()
    text = data.decode()
    assert 'report_timing_summary' in text and 'Device            : xcu280-' in text
    section, = re.findall(r'\| Design Timing Summary\n(.*?)(?=\| Clock Summary)', text, re.S)
    rows = [line.split() for line in section.splitlines()
            if re.match(r'^\s*-?\d+\.\d+\s+-?\d', line)]
    assert len(rows) == 1 and len(rows[0]) == 12
    row = rows[0]
    groups = {}
    for offset, kind in [(0, 'setup'), (4, 'hold'), (8, 'pulse_width')]:
        slack, total_slack = map(float, row[offset:offset + 2])
        failed, total = map(int, row[offset + 2:offset + 4])
        assert 0 <= failed <= total
        groups[kind] = dict(worst_slack_ns=slack, total_negative_slack_ns=total_slack,
                            failing_endpoints=failed, total_endpoints=total,
                            reported_pass=slack >= 0 and total_slack == 0 and failed == 0)
    checks = {}
    for category, count in re.findall(r'checking (\w+) \((\d+)\)', text):
        assert checks.setdefault(category, int(count)) == int(count), 'Inconsistent repeated check counts'
    expected = {'no_clock', 'constant_clock', 'pulse_width_clock', 'unconstrained_internal_endpoints',
                'no_input_delay', 'no_output_delay', 'multiple_clock', 'generated_clocks',
                'loops', 'partial_input_delay', 'partial_output_delay', 'latch_loops'}
    assert set(checks) >= expected
    assert ('Timing constraints are not met.' in section) == (not all(g['reported_pass'] for g in groups.values()))
    report = dict(status='routed_report_timing_and_constraint_coverage_extracted',
                  design_timing=groups, constraint_counts=checks,
                  nonzero_constraint_checks={k: v for k, v in checks.items() if v},
                  input_delay_false_path_exemptions=int(re.search(
                      r'There are (\d+) input ports with no input delay but user has a false path constraint', text)[1]),
                  output_delay_false_path_exemptions=int(re.search(
                      r'There are (\d+) ports with no output delay but user has a false path constraint', text)[1]),
                  source_sha256={str(args.report.resolve()): hashlib.sha256(data).hexdigest(),
                                 str(Path(__file__).resolve()): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
                  scope='Design-level report extraction, with repeated category counts checked. '
                        'Nonzero constraint checks require endpoint-level review and justified exceptions. '
                        'No waivers are inferred. No independent final-clock, checkpoint/image correspondence, '
                        'DRC, adjusted-frequency timing, board measurement or full signoff is established.',
                  verified_signoff=False, board_result=False, research_complete=False)
    assert args.report.read_bytes() == data
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'design_timing', 'nonzero_constraint_checks')}))


if __name__ == '__main__':
    main()
