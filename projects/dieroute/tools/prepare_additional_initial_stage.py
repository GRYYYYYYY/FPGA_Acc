"""Prepare original initial policy with explicit repository paths and cwd."""
import argparse
import ast
import copy
import json
from pathlib import Path
from prepare_additional_fresh_parent import digest


def prepare(attempt, destination):
    root = Path(__file__).resolve().parents[1]
    attempt, destination = attempt.resolve(), destination.resolve()
    template = root / 'work/uniform_capacity_initial_refinement9_20261023'
    original = json.loads((template / 'protocol.json').read_text())
    label = json.loads((attempt / 'parent_preparation.json').read_text())['label']
    case, = [copy.deepcopy(c) for c in original['cases'] if c['label'] == label]
    destination.mkdir()
    changes = []
    for name in ['session_sweep.py', 'native_sweep.py', 'refresh_device.py', 'run_initial.py']:
        text = (template / name).read_text()
        before = 'R = D.parents[1]' if name == 'run_initial.py' else 'R=Path(__file__).resolve().parents[2]'
        after = ('R = ' if name == 'run_initial.py' else 'R=') + 'Path(' + repr(str(root)) + ')'
        assert text.count(before) == 1, name
        adapted = text.replace(before, after)
        assert adapted.replace(after, before) == text
        ast.parse(adapted)
        (destination / name).write_text(adapted)
        changes.append({'file': name, 'before': before, 'after': after})
    view = destination / 'capacity_view'
    view.mkdir()
    targets = {label: attempt / 'capacity',
               'independent_native_review.json': attempt / 'independent_native_review.json',
               'independent_review.terminal.json': attempt / 'capacity_audit.terminal.json',
               'native_protocol.json': attempt / 'capacity/native_protocol.json'}
    for name, target in targets.items():
        (view / name).symlink_to(target, target_is_directory=name == label)
    case.update(repeat_parent_directory=str(attempt / 'parent'),
                parent_prefix=str(attempt / 'parent/route'))
    protocol = {k: copy.deepcopy(v) for k, v in original.items() if k != 'source_sha256'}
    protocol.update(cases=[case], capacity_stage=str(view),
                    scope='One declared fresh case; original policy and budgets unchanged. Preparation is not execution.')
    files = [destination / n for n in ['session_sweep.py', 'native_sweep.py', 'refresh_device.py', 'run_initial.py']]
    files += [Path(protocol[k]) for k in ['frozen_parameter_source', 'validation_vpr', 'session_vpr']]
    files += [attempt / 'parent_preparation.json', attempt / 'capacity_preparation.json', template / 'protocol.json']
    protocol['source_sha256'] = {str(p): digest(p) for p in files}
    (destination / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    guard_source = root / 'work/uniform_capacity_seq3_followup_20261023/guarded_execution.py'
    guard = guard_source.read_text()
    assert guard.count('R=D.parents[1]') == 1
    guard = guard.replace('R=D.parents[1]', 'R=Path(' + repr(str(root)) + ')')
    ast.parse(guard)
    (destination / 'guarded_execution.py').write_text(guard)
    (destination / 'preparation.json').write_text(json.dumps({
        'status': 'generic_initial_prepared_not_executed', 'label': label,
        'path_only_changes': changes, 'guard_change': 'Explicit repository cwd only.',
        'source_sha256': {str(template / n): digest(template / n) for n in
                          ['session_sweep.py', 'native_sweep.py', 'refresh_device.py', 'run_initial.py']},
        'execution_required': 'Fresh capacity audit0; guarded producer then original independent initial auditor.',
        'research_complete': False}, indent=2) + '\n')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(prepare(args.attempt, args.destination))
