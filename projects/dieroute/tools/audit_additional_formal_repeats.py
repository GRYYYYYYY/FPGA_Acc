"""Independently review all declared formal slots; never infer completion from liveness."""
import argparse
import hashlib
import json
from pathlib import Path
import time


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def receipt(directory, name, expected_command):
    launch = read(directory / (name + '.launch.json'))
    terminal = read(directory / (name + '.terminal.json'))
    assert launch['command'] == expected_command
    assert all(terminal[k] == value for k, value in launch.items())
    assert terminal['ended_ns'] >= launch['started_ns']
    return terminal


def audit(directory, output):
    directory = directory.resolve()
    protocol = read(directory / 'protocol.json')
    original = read(protocol['original_case_protocol'])
    labels = [x['label'] for x in original['cases']]
    assert len(labels) == len(set(labels)) == 9
    expected = [(label, repeat) for repeat in range(5) for label in labels]
    slots = protocol['attempts']
    assert [(x['label'], x['repeat']) for x in slots] == expected
    assert protocol['denominator'] == len(slots) == 45
    assert len({x['directory'] for x in slots}) == 45
    for name, value in protocol['source_sha256'].items():
        assert digest(name) == value, name
    started = read(directory / 'execution_started.json')
    assert started['protocol_sha256'] == digest(directory / 'protocol.json')
    terminal = read(directory / 'terminal.json')
    assert terminal['denominator'] == 45 and len(terminal['results']) == 45
    lines = [json.loads(x) for x in (directory / 'outcomes.jsonl').read_text().splitlines()]
    assert lines == terminal['results']
    root = Path(protocol['repository'])
    python = read(directory / 'controller.launch.json')['command'][0]
    groups = {label: [] for label in labels}
    sources = {str(directory / name): digest(directory / name) for name in
               ['protocol.json', 'execution_started.json', 'terminal.json', 'outcomes.jsonl']}
    for slot, outcome in zip(slots, lines):
        assert all(outcome[k] == value for k, value in slot.items())
        attempt = Path(slot['directory'])
        assert attempt.parent == directory / 'attempts'
        saved = directory / 'receipts' / attempt.name
        assert read(saved / 'outcome.json') == outcome
        prep = receipt(saved, 'prepare', [python, str(root / 'tools/prepare_additional_full_attempt.py'),
                                        slot['label'], str(attempt)])
        assert prep['returncode'] == outcome['preparation_returncode']
        if prep['returncode'] != 0:
            assert outcome['status'] == 'preparation_failed'
            assert not (saved / 'full_driver.launch.json').exists()
        else:
            run = receipt(saved, 'full_driver', [python, str(root / 'tools/run_additional_full_attempt.py'),
                                               str(attempt)])
            assert run['returncode'] == outcome['driver_returncode']
            if run['returncode'] != 0:
                assert outcome['status'] == 'execution_failed'
            else:
                assert outcome['status'] == 'final_reviewed'
                done = read(attempt / 'full_attempt_reviewed.json')
                actual = done['final_review_actual_terminal']
                assert actual['returncode'] == 0 and actual['memory_guard_stop_reason'] is None
                report = attempt / 'final_review/audit.json'
                result = read(report)
                assert digest(report) == outcome['final_audit_sha256']
                for item in [done, result]:
                    for name, value in item['source_sha256'].items():
                        assert digest(name) == value, name
                assert result['label'] == slot['label']
                for key in ['joint_quality_pass', 'wirelength', 'cpd_ns',
                            'final_tree_sha256', 'raw_parent_returncode']:
                    assert result[key] == outcome[key]
                assert len(result['source_sha256']) == outcome['verified_final_source_count']
        sources[str(saved / 'outcome.json')] = digest(saved / 'outcome.json')
        groups[slot['label']].append(outcome)
    comparisons = {}
    for label, rows in groups.items():
        assert len(rows) == 5
        passed = [x for x in rows if x['status'] == 'final_reviewed' and x['joint_quality_pass']]
        raw = []
        for row in rows:
            path = Path(row['directory']) / 'parent/router_process_terminal.json'
            raw.append(read(path)['returncode'] if path.exists() else None)
        comparisons[label] = {
            'declared': 5, 'final_joint_passes': len(passed),
            'all_five_final_trees_identical': len(passed) == 5 and
                len({x['final_tree_sha256'] for x in passed}) == 1,
            'raw_parent_failures': sum(code is not None and code != 0 for code in raw),
            'raw_parent_terminal_unobserved': sum(code is None for code in raw),
            'preparation_or_execution_failures': sum(x['status'] != 'final_reviewed' for x in rows)}
    result = {'status': 'all45_actual_slot_receipts_and_final_source_bindings_reviewed',
              'recorded_ns': time.time_ns(), 'denominator': 45, 'cases': comparisons,
              'all45_final_joint_pass': all(x['final_joint_passes'] == 5 for x in comparisons.values()),
              'all_cases_five_repeat_tree_identity': all(x['all_five_final_trees_identical']
                                                       for x in comparisons.values()),
              'source_sha256': sources,
              'scope': 'Formal additional-case cohort only. Raw failures remain failures. '
                       'No no-failure-increase, isolated runtime speedup, board or research completion claim.',
              'research_complete': False, 'board_result': False}
    with output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    audit(args.directory, args.output)
