"""Continue an explicitly audited exhausted-budget parent without extra sweeps."""
import argparse
from pathlib import Path
import sys
import time
import traceback
from prepare_additional_fresh_parent import digest
from continue_additional_fresh_attempt import read, write, live, phase, guarded


def main(attempt):
    attempt = attempt.resolve()
    root = Path(__file__).resolve().parents[1]
    template = root / 'work/uniform_capacity_seq3_followup_20261023'
    original = read(root / 'work/uniform_capacity_initial_refinement9_20261023/protocol.json')
    parameter_source = Path(original['frozen_parameter_source'])
    case_source = root / 'work/uniform_capacity_initial_refinement9_20261023/protocol.json'
    paths = [parameter_source, case_source, template / 'run.py', template / 'protocol.json',
             root / 'tools/audit_additional_exhausted_parent_cwd_v2.py',
             root / 'tools/prepare_additional_budget_mode.py']
    bound = {str(p): digest(p) for p in paths}
    write(attempt / 'exhausted_policy_v2_wait_protocol.json',
          {'source_sha256': bound, 'research_complete': False})
    owner = read(attempt / 'repair_continuation_launch.json')
    while live(owner):
        time.sleep(15)
    assert not (attempt / 'repair_continuation_failure.json').exists()
    read(attempt / 'parent_repair_continuation_terminal.json')
    for name, expected in bound.items():
        assert digest(name) == expected, name
    report_path = attempt / 'budget_outcome_v2.json'
    phase(attempt, 'budget_review_v2_guard', [sys.executable,
          str(root / 'tools/audit_additional_exhausted_parent_cwd_v2.py'), str(attempt),
          str(parameter_source), str(case_source), str(report_path)])
    report = read(report_path)
    label = report['label']
    case, = [c for c in original['cases'] if c['label'] == label]
    case['repeat_parent_directory'] = str(attempt / 'parent')
    case['parent_prefix'] = str(attempt / 'parent/route')
    case_protocol = read(parameter_source)
    case_protocol.update(cases=[case], vpr=original['validation_vpr'],
                         session_vpr=original['session_vpr'])
    case_protocol['source_sha256'] = {str(p): digest(p) for p in
                                    [parameter_source, case_source, report_path]}
    case_protocol_path = attempt / 'budget_case_protocol_v2.json'
    write(case_protocol_path, case_protocol)
    directory = attempt / 'fixed_followup_v2'
    directory.mkdir()
    (directory / 'execution').mkdir()
    script = (template / 'run.py').read_text()
    old = "initial['label'] == 'seq_seed3'"
    assert script.count(old) == 1
    script = script.replace(old, "initial['label'] == " + repr(label))
    script = script.replace('R = D.parents[1]', 'R = Path(' + repr(str(root)) + ')')
    old = "initial['status'] == 'prospective_initial_case_decisions_and_native_provenance_reviewed'"
    assert script.count(old) == 1
    script = script.replace(old, "initial['status'] == 'fresh_parent_budget_exhausted_capacity_outcome_reviewed'")
    (directory / 'run.py').write_text(script)
    (directory / 'guarded_execution.py').write_bytes((attempt / 'guarded_execution.py').read_bytes())
    protocol = read(template / 'protocol.json')
    sources = dict(protocol['source_sha256'])
    for name in [protocol['case_protocol'], str(template / 'run.py'), protocol['preparer']]:
        del sources[name]
    protocol.update(initial_terminal=str(attempt / 'capacity_audit.terminal.json'),
                    initial_report=str(report_path), case_protocol=str(case_protocol_path),
                    preparer=str(root / 'tools/prepare_additional_budget_mode.py'),
                    scope='Explicit exhausted-budget branch; no extra initial sweep or refresh.')
    for name in [str(case_protocol_path), str(directory / 'run.py'), protocol['preparer']]:
        sources[name] = digest(name)
    protocol['source_sha256'] = sources
    write(directory / 'protocol.json', protocol)
    sources = dict(sources)
    for p in [directory / 'protocol.json', directory / 'guarded_execution.py']:
        sources[str(p)] = digest(p)
    write(directory / 'native_protocol.json',
          {'cases': [{'label': 'execution', 'commands': {
              'followup': [sys.executable, str(directory / 'run.py')]}}],
           'source_sha256': sources, 'research_complete': False})
    guarded(directory)
    final = read(directory / 'manifest.json')
    write(attempt / 'exhausted_policy_v2_terminal.json', {
        'status': 'budget_exhausted_policy_terminal_final_attempt_audit_required',
        'final_report': final['final_report'], 'additional_initial_sweeps_executed': 0,
        'research_complete': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=Path)
    args = parser.parse_args()
    try:
        main(args.attempt)
    except BaseException:
        write(args.attempt / 'exhausted_policy_v2_failure.json',
              {'error': traceback.format_exc(), 'research_complete': False})
        raise
