"""Apply the frozen capacity fallback only to cases that exhausted both modes."""
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
        temp = directory / 'manifest.tmp'
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(directory / 'manifest.json')

    def verify():
        for name, expected in protocol['source_sha256'].items():
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name

    def live():
        owner = protocol['mode_owner']
        path = Path('/proc') / str(owner['pid']) / 'stat'
        if not path.exists():
            return False
        text = path.read_text()
        fields = text[text.rfind(')') + 2:].split()
        return fields[0] != 'Z' and fields[19] == owner['start_ticks']

    def command(args, log, row):
        started = time.monotonic_ns()
        with log.open('x') as stream:
            child = subprocess.Popen(args, cwd=protocol['cwd'], stdout=stream, stderr=subprocess.STDOUT)
            row['active_pid'] = child.pid
            save()
            code = child.wait()
        row.update(last_returncode=code, last_command_wall_ns=time.monotonic_ns() - started)
        save()
        return code

    try:
        verify()
        save()
        terminal = ['joint_pass_after_initial_stages_no_modes_required', 'joint_pass_after_native_mode',
                    'both_native_modes_exhausted_capacity_fallback_required', 'initial_failure_retained_no_native_modes',
                    'native_mode_execution_error_retained_no_replay', 'native_mode_audit_error_retained_no_replay',
                    'native_mode_termination_outcome_retained_no_transition']
        for label in protocol['labels']:
            state.update(status='waiting_for_original_mode_case', active_case=label)
            save()
            while True:
                try:
                    modes = json.loads(Path(protocol['mode_manifest']).read_text())
                except (OSError, json.JSONDecodeError):
                    modes = {}
                result = next((v for v in modes.get('cases', []) if v['label'] == label), None)
                if result and result.get('status') in terminal:
                    break
                assert modes.get('status') != 'native_mode_queue_stopped_requires_review', modes.get('error')
                assert live(), 'Original mode owner missing; reconcile without restart'
                time.sleep(10)
            row = {'label': label, 'mode_status': result['status']}
            state['cases'].append(row)
            (directory / (label + '_mode_snapshot.json')).write_text(json.dumps(result, indent=2) + '\n')
            if result['status'] in terminal[:2]:
                report = json.loads(Path(result['final_report']).read_text())
                assert report['label'] == label
                assert report.get('joint_quality_pass', report.get('final_original_baseline_joint_pass')) is True
                row.update(status='joint_pass_before_capacity_fallback', joint_quality_pass=True,
                           final_report=result['final_report'])
            elif result['status'] != terminal[2]:
                row.update(status='upstream_failure_retained_no_capacity_fallback', joint_quality_pass=False)
            else:
                verify()
                mode = Path(result['modes'][-1]['report']).parent
                mp = json.loads((mode / 'protocol.json').read_text())
                assert mp['prospective_label'] == label and mp['prospective_mode'] == 'delay'
                output = directory / label
                state['status'] = 'running_preregistered_capacity_fallback'
                save()
                if command(['python3', protocol['runner'], str(mode), str(output), '--run'],
                           directory / (label + '_execution.log'), row):
                    row.update(status='capacity_fallback_execution_error_retained', joint_quality_pass=False)
                    save()
                    continue
                row['fallback_wall_ns'] = row['last_command_wall_ns']
                if command(['python3', protocol['auditor'], str(output)], directory / (label + '_audit.log'), row):
                    row.update(status='capacity_fallback_audit_error_retained', joint_quality_pass=False)
                    save()
                    continue
                audit = json.loads((output / 'fallback_audit.json').read_text())
                assert audit['label'] == label
                row.update(status='capacity_fallback_terminal_independently_reviewed',
                           joint_quality_pass=audit['joint_quality_pass'], final_report=str(output / 'fallback_audit.json'),
                           audit_wall_ns=row['last_command_wall_ns'])
            save()
        state['status'] = 'five_prospective_policy_cases_terminal_require_final_cohort_audit'
        save()
    except BaseException:
        state.update(status='capacity_fallback_queue_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
