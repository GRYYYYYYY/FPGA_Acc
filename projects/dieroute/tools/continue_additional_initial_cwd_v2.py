"""Explicit new initial stage after a retained pre-algorithm cwd failure."""
from pathlib import Path
import sys
import traceback
from continue_additional_fresh_attempt import read, write, guarded
from prepare_additional_fresh_parent import digest


def main(attempt):
    stage = attempt / 'initial_v2'
    prep = read(attempt / 'initial_v2_preparation.json')
    for name, expected in prep['source_sha256'].items():
        assert digest(name) == expected, name
    assert not (attempt / 'initial/manifest.json').exists()
    assert read(attempt / 'initial/execution/initial.terminal.json')['returncode'] == 1
    assert read(attempt / 'capacity_audit.terminal.json')['returncode'] == 0
    guarded(stage)
    label = read(attempt / 'parent_preparation.json')['label']
    directory = attempt / 'initial_v2_review_guard'
    directory.mkdir()
    (directory / 'execution').mkdir()
    guard = directory / 'guarded_execution.py'
    guard.write_bytes((stage / 'guarded_execution.py').read_bytes())
    auditor = attempt / 'initial_auditor/audit_initial_case.py'
    command = [sys.executable, str(auditor), str(stage), label,
               str(attempt / 'initial_v2_review')]
    write(directory / 'native_protocol.json', {
        'cases': [{'label': 'execution', 'commands': {'review': command}}],
        'source_sha256': {str(auditor): digest(auditor), str(guard): digest(guard)},
        'research_complete': False})
    terminal = guarded(directory)[0]
    write(attempt / 'initial_v2_audit.terminal.json', terminal)
    report = read(attempt / 'initial_v2_review/audit.json')
    write(attempt / 'initial_v2_continuation_terminal.json', {
        'status': 'corrected_cwd_initial_independently_reviewed_followup_pending',
        'joint_quality_pass': report['joint_quality_pass'],
        'research_complete': False})


if __name__ == '__main__':
    attempt = Path(sys.argv[1]).resolve()
    try:
        main(attempt)
    except BaseException:
        write(attempt / 'initial_v2_continuation_failure.json',
              {'error': traceback.format_exc(), 'research_complete': False})
        raise
