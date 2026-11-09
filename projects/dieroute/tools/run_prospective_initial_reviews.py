"""Audit completed prospective initial cases while preserving every outcome."""
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
        owner = protocol['original_owner']
        path = Path('/proc') / str(owner['pid']) / 'stat'
        if not path.exists():
            return False
        text = path.read_text()
        fields = text[text.rfind(')') + 2:].split()
        return fields[0] != 'Z' and fields[19] == owner['start_ticks']

    try:
        verify()
        save()
        terminal = ['initial_sweep_refresh_terminal_requires_independent_review',
                    'parent_failure_retained_no_refinement', 'frozen_initial_sweep_budget_exhausted',
                    'initial_refinement_error_retained_no_replay']
        for case in protocol['cases']:
            label = case['label']
            state.update(status='waiting_for_original_initial_case', active_case=label)
            save()
            while True:
                try:
                    initial = json.loads(Path(protocol['initial_manifest']).read_text())
                except (OSError, json.JSONDecodeError):
                    initial = {}
                result = next((v for v in initial.get('cases', []) if v['label'] == label), None)
                if result and result.get('status') in terminal:
                    break
                assert initial.get('status') != 'initial_refinement_queue_stopped_requires_review', initial.get('error')
                assert live(), 'Original initial-stage owner missing; no restart'
                time.sleep(10)
            row = {'label': label, 'producer_status': result['status']}
            state['cases'].append(row)
            if result['status'] != terminal[0]:
                row['status'] = 'producer_failure_or_budget_outcome_retained'
                save()
                continue
            verify()
            state['status'] = 'auditing_completed_initial_case'
            save()
            start = time.monotonic_ns()
            with (directory / (label + '.log')).open('x') as log:
                child = subprocess.Popen(case['command'], cwd=protocol['cwd'], stdout=log, stderr=subprocess.STDOUT)
                row['audit_pid'] = child.pid
                save()
                code = child.wait()
            row.update(returncode=code, audit_wall_ns=time.monotonic_ns() - start)
            if code:
                row['status'] = 'independent_case_audit_failed_requires_review'
            else:
                audit = json.loads(Path(case['report']).read_text())
                assert audit['label'] == label and audit['status'] == 'prospective_initial_case_decisions_and_native_provenance_reviewed'
                row.update(status='independent_initial_case_audit_passed',
                           joint_quality_pass=audit['joint_quality_pass'], report=case['report'])
            save()
        state['status'] = 'five_prospective_initial_case_reviews_terminal_requires_interpretation'
        save()
    except BaseException:
        state.update(status='initial_case_review_queue_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
