"""Execute one prepared fresh full policy; retain failures without implicit replay."""
import argparse
import json
from pathlib import Path
import sys
import traceback
from prepare_additional_fresh_parent import digest
from continue_additional_fresh_attempt import read, write, guarded, phase
from prepare_additional_fixed_followup import prepare as followup_prepare


def main(attempt):
    root = Path(__file__).resolve().parents[1]
    work = root / 'work'
    attempt = attempt.resolve()
    config = read(attempt / 'full_preparation.json')
    for name, expected in config['source_sha256'].items():
        assert digest(name) == expected, name
    assert not (attempt / 'execution_started.json').exists(), 'No implicit replay'
    tools = ['run_additional_full_attempt.py', 'review_additional_parent_for_repair.py',
             'audit_additional_fresh_capacity.py', 'audit_additional_exhausted_parent_cwd_v2.py',
             'audit_additional_exhausted_parent.py', 'prepare_additional_fixed_followup.py',
             'audit_additional_full_attempt.py', 'continue_additional_fresh_attempt.py',
             'prepare_additional_fresh_parent.py', 'prepare_additional_budget_mode.py']
    write(attempt / 'execution_started.json', {
        'status': 'fresh_full_policy_started',
        'source_sha256': {str(root / 'tools' / n): digest(root / 'tools' / n) for n in tools},
        'research_complete': False})
    # The existing guard records raw3 and then raises its success assertion.
    # Accept only this explicit raw-router outcome after verifying actual receipts.
    try:
        guarded(attempt)
    except AssertionError:
        assert read(attempt / 'controller_guard.terminal.json')['returncode'] == 0
        assert not (attempt / 'native_failure.json').exists()
        result, = read(attempt / 'native_terminal.json')['results']
        step, = result['steps']
        assert step['returncode'] == 3 and step['memory_guard_stop_reason'] is None
        assert step == read(attempt / 'parent_execution/fresh_parent.terminal.json')
        command = read(attempt / 'native_protocol.json')['cases'][0]['commands']['fresh_parent']
        assert step['command'] == command
        assert read(attempt / 'parent/router_process_terminal.json')['returncode'] == 3
    phase(attempt, 'raw_parent_review_guard', [sys.executable,
          str(root / 'tools/review_additional_parent_for_repair.py'), str(attempt)])
    assert read(attempt / 'parent_repair_eligibility.json')['repair_eligible']
    guarded(attempt / 'capacity')
    terminal = phase(attempt, 'capacity_review_guard', [sys.executable,
                     str(root / 'tools/audit_additional_fresh_capacity.py'), str(attempt)])
    write(attempt / 'capacity_audit.terminal.json', terminal)
    original_source = work / 'uniform_capacity_initial_refinement9_20261023/protocol.json'
    original = read(original_source)
    parameter_source = Path(original['frozen_parameter_source'])
    parameters = read(parameter_source)
    iterations = read(attempt / 'parent/route.json')['iterations']
    assert parameters['minimum_prior_timing_iterations'] <= iterations <= parameters['maximum_total_routing_sweeps']
    exhausted = iterations == parameters['maximum_total_routing_sweeps']
    write(attempt / 'policy_branch.json', {
        'kind': 'budget_exhausted' if exhausted else 'initial',
        'parent_iterations': iterations, 'parameter_source': str(parameter_source),
        'source_sha256': {str(parameter_source): digest(parameter_source)},
        'research_complete': False})
    if exhausted:
        report = attempt / 'budget_outcome.json'
        phase(attempt, 'budget_review_guard', [sys.executable,
              str(root / 'tools/audit_additional_exhausted_parent_cwd_v2.py'), str(attempt),
              str(parameter_source), str(original_source), str(report)])
        case, = read(attempt / 'initial/protocol.json')['cases']
        cp = read(parameter_source)
        cp.update(cases=[case], vpr=original['validation_vpr'], session_vpr=original['session_vpr'])
        cp['source_sha256'] = {str(p): digest(p) for p in [parameter_source, original_source, report]}
        case_protocol = attempt / 'budget_case_protocol.json'
        write(case_protocol, cp)
        prior_terminal = attempt / 'capacity_audit.terminal.json'
    else:
        initial = attempt / 'initial'
        (initial / 'execution').mkdir()
        source = read(initial / 'protocol.json')['source_sha256']
        source.update({str(p): digest(p) for p in [initial / 'protocol.json', initial / 'guarded_execution.py']})
        write(initial / 'native_protocol.json', {
            'cases': [{'label': 'execution', 'commands': {'initial': [sys.executable, str(initial / 'run_initial.py')]}}],
            'source_sha256': source, 'research_complete': False})
        guarded(initial)
        label = config['label']
        terminal = phase(attempt, 'initial_review_guard', [sys.executable,
                         str(attempt / 'initial_auditor/audit_initial_case.py'), str(initial),
                         label, str(attempt / 'initial_review')])
        prior_terminal = attempt / 'initial_audit.terminal.json'
        write(prior_terminal, terminal)
        report = attempt / 'initial_review/audit.json'
        case_protocol = initial / label / 'protocol.json'
    followup_prepare(case_protocol, report, prior_terminal, attempt / 'fixed_followup')
    guarded(attempt / 'fixed_followup')
    terminal = phase(attempt, 'final_review_guard', [sys.executable,
                     str(root / 'tools/audit_additional_full_attempt.py'),
                     str(attempt), str(attempt / 'final_review')])
    result = read(attempt / 'final_review/audit.json')
    write(attempt / 'full_attempt_reviewed.json', {
        'status': 'one_generic_fresh_full_attempt_independently_reviewed',
        'joint_quality_pass': result['joint_quality_pass'],
        'wirelength': result['wirelength'], 'cpd_ns': result['cpd_ns'],
        'final_review_actual_terminal': terminal,
        'source_sha256': {str(attempt / 'final_review/audit.json'): digest(attempt / 'final_review/audit.json')},
        'research_complete': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=Path)
    args = parser.parse_args()
    try:
        main(args.attempt)
    except BaseException:
        write(args.attempt / 'full_execution_failure.json',
              {'error': traceback.format_exc(), 'research_complete': False})
        raise
