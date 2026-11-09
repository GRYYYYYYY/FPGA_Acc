"""Run the two frozen native-guided modes after an independent initial audit."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback


def main():
    directory = Path(sys.argv[1]).resolve()
    protocol = json.loads((directory / 'protocol.json').read_text())
    assert not (directory / 'manifest.json').exists(), 'No implicit replay'
    state = {'status': 'checking_sources', 'pid': os.getpid(), 'cases': [], 'research_complete': False}

    def save():
        temporary = directory / 'manifest.tmp'
        temporary.write_text(json.dumps(state, indent=2) + '\n')
        temporary.replace(directory / 'manifest.json')

    def verify():
        for name, expected in protocol['source_sha256'].items():
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name

    def live():
        owner = protocol['review_owner']
        path = Path('/proc') / str(owner['pid']) / 'stat'
        if not path.exists():
            return False
        text = path.read_text()
        fields = text[text.rfind(')') + 2:].split()
        return fields[0] != 'Z' and fields[19] == owner['start_ticks']

    def run(command, path, row):
        begin = time.monotonic_ns()
        with path.open('x') as stream:
            child = subprocess.Popen(command, cwd=protocol['cwd'], stdout=stream, stderr=subprocess.STDOUT)
            row['active_pid'] = child.pid
            save()
            code = child.wait()
        row['last_command_wall_ns'] = time.monotonic_ns() - begin
        row['last_returncode'] = code
        save()
        return code

    try:
        verify()
        save()
        for case in protocol['cases']:
            label = case['label']
            state.update(status='waiting_for_independent_initial_review', active_case=label)
            save()
            while True:
                try:
                    reviews = json.loads(Path(protocol['review_manifest']).read_text())
                except (OSError, json.JSONDecodeError):
                    reviews = {}
                reviewed = next((v for v in reviews.get('cases', []) if v['label'] == label), None)
                if reviewed and reviewed.get('status') in [
                    'independent_initial_case_audit_passed', 'producer_failure_or_budget_outcome_retained',
                    'independent_case_audit_failed_requires_review']:
                    break
                assert reviews.get('status') != 'initial_case_review_queue_stopped_requires_review', reviews.get('error')
                assert live(), 'Original initial-review owner missing; reconcile without restart'
                time.sleep(10)
            row = {'label': label, 'initial_review_status': reviewed['status'], 'modes': []}
            state['cases'].append(row)
            if reviewed['status'] != 'independent_initial_case_audit_passed':
                row['status'] = 'initial_failure_retained_no_native_modes'
                save()
                continue
            initial_report = Path(reviewed['report'])
            initial = json.loads(initial_report.read_text())
            assert initial['label'] == label and initial['status'] == 'prospective_initial_case_decisions_and_native_provenance_reviewed'
            row['initial_report'] = str(initial_report)
            if initial['joint_quality_pass']:
                row.update(status='joint_pass_after_initial_stages_no_modes_required', final_report=str(initial_report))
                save()
                continue
            folder = directory / label
            folder.mkdir()
            prior = None
            verify()
            for mode in ['wirelength', 'delay']:
                output = folder / mode
                record = {'mode': mode, 'status': 'preparing_and_running'}
                row['modes'].append(record)
                state['status'] = 'running_frozen_native_mode'
                save()
                command = ['python3', protocol['preparer'], protocol['baselines'], protocol['roundtrip'], protocol['costs'],
                           case['case_protocol'], str(initial_report), mode, str(output), '--run']
                if prior is not None:
                    command += ['--prior-mode', str(prior)]
                if run(command, folder / (mode + '_execution.log'), record):
                    row['status'] = 'native_mode_execution_error_retained_no_replay'
                    record['status'] = 'execution_error_requires_review'
                    break
                record['execution_wall_ns'] = record['last_command_wall_ns']
                termination = json.loads((output / 'manifest.json').read_text())['status']
                record['termination'] = termination
                if termination not in ['experiment_terminal_original_baseline_joint_quality_pass',
                                       'experiment_terminal_all_selected_tasks_exhausted',
                                       'experiment_terminal_frozen_stage_budget_exhausted',
                                       'experiment_terminal_no_selected_regression']:
                    record['status'] = 'unregistered_termination_requires_review'
                    row['status'] = 'native_mode_termination_outcome_retained_no_transition'
                    break
                record['status'] = 'independent_mode_audit_running'
                save()
                if run(['python3', protocol['auditor'], str(output)], folder / (mode + '_audit.log'), record):
                    row['status'] = 'native_mode_audit_error_retained_no_replay'
                    record['status'] = 'audit_error_requires_review'
                    break
                report = output / 'mode_audit.json'
                audit = json.loads(report.read_text())
                assert audit['label'] == label and audit['mode'] == mode
                record.update(status='terminal_independently_reviewed', audit_wall_ns=record['last_command_wall_ns'], report=str(report))
                row['current_state'] = audit['current_state']
                if audit['final_original_baseline_joint_pass']:
                    row.update(status='joint_pass_after_native_mode', final_report=str(report))
                    break
                prior = output
                save()
            else:
                row['status'] = 'both_native_modes_exhausted_capacity_fallback_required'
            save()
        state['status'] = 'five_prospective_native_mode_cases_terminal_requires_interpretation'
        save()
    except BaseException:
        state.update(status='native_mode_queue_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
