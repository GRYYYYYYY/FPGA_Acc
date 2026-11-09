"""Run a frozen nine-case, five-repeat full-policy cohort serially without retries."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def validate(directory):
    protocol = read(directory / 'protocol.json')
    expected = [case['label'] for case in read(protocol['original_case_protocol'])['cases']]
    assert len(expected) == 9 and len(set(expected)) == 9
    assert [(x['label'], x['repeat']) for x in protocol['attempts']] == [
        (label, repeat) for repeat in range(5) for label in expected]
    paths = [x['directory'] for x in protocol['attempts']]
    assert len(set(paths)) == 45
    assert all(Path(p).parent == directory / 'attempts' for p in paths)
    for name, value in protocol['source_sha256'].items():
        assert digest(name) == value, name
    return protocol


def execute(command, directory, name, cwd):
    with (directory / (name + '.stdout')).open('x') as out, (directory / (name + '.stderr')).open('x') as err:
        child = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL,
                                 stdout=out, stderr=err, start_new_session=True)
        fields = Path('/proc', str(child.pid), 'stat').read_text().rsplit(')', 1)[1].split()
        launch = {'pid': child.pid, 'start_ticks': fields[19], 'command': command,
                  'cwd': str(cwd), 'started_ns': time.time_ns()}
        write(directory / (name + '.launch.json'), launch)
        code = child.wait()
    terminal = {**launch, 'returncode': code, 'ended_ns': time.time_ns()}
    write(directory / (name + '.terminal.json'), terminal)
    return terminal


def main(directory, validate_only=False):
    directory = directory.resolve()
    protocol = validate(directory)
    if validate_only:
        print('Validated original nine labels, all45 slots and frozen source hashes')
        return
    write(directory / 'execution_started.json', {
        'recorded_ns': time.time_ns(), 'protocol_sha256': digest(directory / 'protocol.json'),
        'research_complete': False})
    root = Path(protocol['repository'])
    results = []
    for slot in protocol['attempts']:
        # Fail closed on source changes, before the next independent attempt.
        validate(directory)
        attempt = Path(slot['directory'])
        assert not attempt.exists(), 'No replay or implicit replacement'
        receipts = directory / 'receipts' / attempt.name
        receipts.mkdir()
        prep = execute([sys.executable, str(root / 'tools/prepare_additional_full_attempt.py'),
                        slot['label'], str(attempt)], receipts, 'prepare', root)
        row = {**slot, 'preparation_returncode': prep['returncode'],
               'status': 'preparation_failed', 'joint_quality_pass': False}
        if prep['returncode'] == 0:
            terminal = execute([sys.executable, str(root / 'tools/run_additional_full_attempt.py'),
                                str(attempt)], receipts, 'full_driver', root)
            row['driver_returncode'] = terminal['returncode']
            row['status'] = 'execution_failed'
            if terminal['returncode'] == 0:
                done = read(attempt / 'full_attempt_reviewed.json')
                for name, value in done['source_sha256'].items():
                    assert digest(name) == value, name
                audit = read(attempt / 'final_review/audit.json')
                actual = done['final_review_actual_terminal']
                assert actual['returncode'] == 0 and actual['memory_guard_stop_reason'] is None
                for name, value in audit['source_sha256'].items():
                    assert digest(name) == value, name
                assert audit['label'] == slot['label']
                row.update(status='final_reviewed', joint_quality_pass=audit['joint_quality_pass'],
                           wirelength=audit['wirelength'], cpd_ns=audit['cpd_ns'],
                           final_tree_sha256=audit['final_tree_sha256'],
                           raw_parent_returncode=audit['raw_parent_returncode'],
                           final_audit_sha256=digest(attempt / 'final_review/audit.json'),
                           verified_final_source_count=len(audit['source_sha256']))
        # A failed slot remains in the fixed denominator; no replacement or retry.
        write(receipts / 'outcome.json', row)
        results.append(row)
        with (directory / 'outcomes.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')
    write(directory / 'terminal.json', {
        'status': 'all45_declared_slots_processed_requires_independent_cohort_review',
        'results': results, 'denominator': 45, 'research_complete': False,
        'board_result': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    main(args.directory, args.validate_only)
