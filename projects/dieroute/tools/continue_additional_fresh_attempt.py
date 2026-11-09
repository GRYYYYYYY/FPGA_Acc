"""Continue one fresh integration attempt through audited initial refinement."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import time
import traceback
from prepare_additional_fresh_parent import digest


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def live(receipt):
    try:
        fields = Path('/proc', str(receipt['pid']), 'stat').read_text().rsplit(')', 1)[1].split()
        return fields[0] != 'Z' and fields[19] == receipt['start_ticks']
    except FileNotFoundError:
        return False


def guarded(directory):
    assert not (directory / 'controller_guard.launch.json').exists(), 'No replay'
    command = [sys.executable, str(directory / 'guarded_execution.py')]
    with (directory / 'controller_guard.stdout').open('x') as out, (directory / 'controller_guard.stderr').open('x') as err:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=out,
                                 stderr=err, start_new_session=True)
        fields = Path('/proc', str(child.pid), 'stat').read_text().rsplit(')', 1)[1].split()
        receipt = {'pid': child.pid, 'start_ticks': fields[19],
                   'command': command, 'started_ns': time.time_ns()}
        write(directory / 'controller_guard.launch.json', receipt)
        code = child.wait()
    write(directory / 'controller_guard.terminal.json',
          {**receipt, 'returncode': code, 'ended_ns': time.time_ns()})
    assert code == 0
    assert not (directory / 'native_failure.json').exists()
    result = read(directory / 'native_terminal.json')
    assert len(result['results']) == 1
    steps = result['results'][0]['steps']
    expected = next(iter(read(directory / 'native_protocol.json')['cases']))['commands']
    assert len(steps) == len(expected)
    assert all(s['returncode'] == 0 and s['memory_guard_stop_reason'] is None for s in steps)
    return steps


def phase(attempt, name, command):
    directory = attempt / name
    directory.mkdir()
    (directory / 'execution').mkdir()
    template = attempt / 'guarded_execution.py'
    (directory / 'guarded_execution.py').write_bytes(template.read_bytes())
    sources = {str(Path(command[1])): digest(command[1]),
               str(directory / 'guarded_execution.py'): digest(template)}
    write(directory / 'native_protocol.json',
          {'cases': [{'label': 'execution', 'commands': {'run': command}}],
           'source_sha256': sources, 'research_complete': False})
    return guarded(directory)[0]


def main(attempt):
    attempt = attempt.resolve()
    root = Path(__file__).resolve().parents[1]
    owner = read(attempt / 'guard_launch.json')
    while live(owner):
        time.sleep(15)
    assert not (attempt / 'native_failure.json').exists()
    terminal = read(attempt / 'native_terminal.json')
    steps = terminal['results'][0]['steps']
    assert len(steps) == 5 and all(s['returncode'] == 0 and
                                 s['memory_guard_stop_reason'] is None for s in steps)
    guarded(attempt / 'capacity')
    receipt = phase(attempt, 'capacity_review_guard',
                    [sys.executable, str(root / 'tools/audit_additional_fresh_capacity.py'), str(attempt)])
    # Exact copy of an actual process terminal, consumed by the existing ABI.
    write(attempt / 'capacity_audit.terminal.json', receipt)
    initial = attempt / 'initial'
    (initial / 'execution').mkdir()
    (initial / 'guarded_execution.py').write_bytes((attempt / 'guarded_execution.py').read_bytes())
    protocol = read(initial / 'protocol.json')
    sources = dict(protocol['source_sha256'])
    for file in [initial / 'protocol.json', initial / 'guarded_execution.py']:
        sources[str(file)] = digest(file)
    write(initial / 'native_protocol.json',
          {'cases': [{'label': 'execution', 'commands': {
              'initial': [sys.executable, str(initial / 'run_initial.py')]}}],
           'source_sha256': sources, 'research_complete': False})
    guarded(initial)
    label = read(attempt / 'parent_preparation.json')['label']
    receipt = phase(attempt, 'initial_review_guard',
                    [sys.executable, str(attempt / 'initial_auditor/audit_initial_case.py'),
                     str(initial), label, str(attempt / 'initial_review')])
    write(attempt / 'initial_audit.terminal.json', receipt)
    report = read(attempt / 'initial_review/audit.json')
    write(attempt / 'continuation_terminal.json',
          {'status': 'fresh_initial_audited_fixed_followup_and_final_audit_still_required',
           'initial_joint_quality_pass': report['joint_quality_pass'],
           'research_complete': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=Path)
    args = parser.parse_args()
    try:
        main(args.attempt)
    except BaseException:
        write(args.attempt / 'continuation_failure.json',
              {'error': traceback.format_exc(), 'research_complete': False})
        raise
