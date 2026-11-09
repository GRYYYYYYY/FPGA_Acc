"""Prepare one new parent-routing recipe without changing frozen routing policy."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def prepare(frozen, label, destination):
    frozen, destination = frozen.resolve(), destination.resolve()
    protocol = json.loads((frozen / 'protocol.json').read_text())
    declared = [c for c in protocol['cases'] if c['label'] == label]
    if len(declared) != 1:
        raise ValueError('Case must occur exactly once in original declared cohort')
    original = frozen / 'recipes' / label
    pair = original / 'pair.json'
    recipe = json.loads(pair.read_text())
    if len(recipe['steps']) != 1:
        raise ValueError('Expected original single routing step')
    tasks = original / 'input.tasks'
    source = (original / 'source').resolve(strict=True)
    runner, build = Path(protocol['runner']), Path(protocol['timing_build'])
    audit = build / 'build_dependency_audit.json'
    build_info = json.loads(audit.read_text())
    if digest(build_info['binary']) != build_info['binary_sha256']:
        raise ValueError('Frozen timing binary digest mismatch')
    destination.mkdir(exist_ok=False, parents=True)
    target = destination / 'recipe'
    target.mkdir()
    (target / 'source').symlink_to(source, target_is_directory=True)
    (target / 'input.tasks').symlink_to(tasks)
    # The original runner substitutes only command[3] with the new output.
    (target / 'pair.json').write_bytes(pair.read_bytes())
    result = {
        'status': 'fresh_parent_recipe_prepared_execution_not_started',
        'label': label,
        'command': [sys.executable, str(runner), str(target / 'pair.json'),
                    str(build), str(destination / 'parent')],
        'source_sha256': {str(p): digest(p) for p in
                          [pair, tasks, runner, audit, Path(__file__).resolve()]},
        'routing_recipe_byte_identical': True,
        'scope': 'Preparation only. Fresh routing and independent parent/native/capacity '
                 'audits plus all later policy stages remain required.',
        'research_complete': False,
    }
    (destination / 'parent_preparation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('frozen', type=Path)
    parser.add_argument('label')
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.frozen, args.label, args.destination), indent=2))
