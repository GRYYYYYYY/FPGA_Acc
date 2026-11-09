"""Prepare original fixed followup for one independently reviewed fresh case."""
import argparse
import ast
import json
import sys
from pathlib import Path
from prepare_additional_fresh_parent import digest


def prepare(case_protocol, report_path, terminal_path, destination):
    root = Path(__file__).resolve().parents[1]
    template = root / 'work/uniform_capacity_seq3_followup_20261023'
    case_protocol, report_path, terminal_path, destination = (
        p.resolve() for p in (case_protocol, report_path, terminal_path, destination))
    report = json.loads(report_path.read_text())
    terminal = json.loads(terminal_path.read_text())
    assert terminal['returncode'] == 0 and terminal['memory_guard_stop_reason'] is None
    case, = json.loads(case_protocol.read_text())['cases']
    assert report['label'] == case['label']
    regular = 'prospective_initial_case_decisions_and_native_provenance_reviewed'
    exhausted = 'fresh_parent_budget_exhausted_capacity_outcome_reviewed'
    assert report['status'] in [regular, exhausted]
    for name, expected in report['source_sha256'].items():
        assert digest(name) == expected, name
    destination.mkdir()
    (destination / 'execution').mkdir()
    script = (template / 'run.py').read_text()
    changes = [("initial['label'] == 'seq_seed3'", "initial['label'] == " + repr(case['label'])),
               ('R = D.parents[1]', 'R = Path(' + repr(str(root)) + ')')]
    if report['status'] == exhausted:
        assert report['parent_iterations'] == report['maximum_total_routing_sweeps']
        assert report['additional_initial_sweeps_executed'] == 0
        changes.append(("initial['status'] == " + repr(regular),
                        "initial['status'] == " + repr(exhausted)))
    for before, after in changes:
        assert script.count(before) == 1
        script = script.replace(before, after)
    ast.parse(script)
    (destination / 'run.py').write_text(script)
    guard = (template / 'guarded_execution.py').read_text()
    assert guard.count('R=D.parents[1]') == 1
    guard = guard.replace('R=D.parents[1]', 'R=Path(' + repr(str(root)) + ')')
    (destination / 'guarded_execution.py').write_text(guard)
    protocol = json.loads((template / 'protocol.json').read_text())
    sources = dict(protocol['source_sha256'])
    for name in [protocol['case_protocol'], str(template / 'run.py')]:
        del sources[name]
    if report['status'] == exhausted:
        del sources[protocol['preparer']]
        protocol['preparer'] = str(root / 'tools/prepare_additional_budget_mode.py')
        sources[protocol['preparer']] = digest(protocol['preparer'])
    protocol.update(initial_terminal=str(terminal_path), initial_report=str(report_path),
                    case_protocol=str(case_protocol),
                    scope='One fresh case original fixed policy; not a repeated cohort or benchmark.')
    for path in [case_protocol, report_path, terminal_path, destination / 'run.py']:
        sources[str(path)] = digest(path)
    for name, expected in sources.items():
        assert digest(name) == expected, name
    protocol['source_sha256'] = sources
    (destination / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    for path in [destination / 'protocol.json', destination / 'guarded_execution.py']:
        sources[str(path)] = digest(path)
    (destination / 'native_protocol.json').write_text(json.dumps({
        'cases': [{'label': 'execution', 'commands': {
            'followup': [sys.executable, str(destination / 'run.py')]}}],
        'source_sha256': sources, 'research_complete': False}, indent=2) + '\n')
    (destination / 'preparation.json').write_text(json.dumps({
        'status': 'generic_fixed_followup_prepared_not_executed',
        'path_label_status_adaptations': changes,
        'source_sha256': {str(template / 'run.py'): digest(template / 'run.py'),
                          str(destination / 'native_protocol.json'): digest(destination / 'native_protocol.json')},
        'policy_order': ['skip_if_initial_joint_pass', 'wirelength', 'delay', 'capacity_fallback'],
        'research_complete': False}, indent=2) + '\n')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['case_protocol', 'report', 'terminal', 'destination']:
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    print(prepare(args.case_protocol, args.report, args.terminal, args.destination))
