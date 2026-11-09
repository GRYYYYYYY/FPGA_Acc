"""Consistently rehash five copied repetitions to challenge semantic/version replay."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from rr_resource_version_replay import fnv_words


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('variant', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    variant, output = args.variant.resolve(), args.output.resolve()
    output.mkdir(exist_ok=False)
    execution = json.loads((variant / 'protocol.json').read_text())
    original = Path(execution['commands'][2][4])
    manifest = json.loads((original / 'pair.json').read_text())
    assert manifest['status'] == 'completed' and manifest['configuration']['supplemental_transaction_mode'] == 2
    mode = 'downstream_bounded'
    assert set(manifest['modes']) == {mode}
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    original_hashes = {str(original / f'{mode}_{i}.{suffix}'): digest
                       for i, hashes in enumerate(manifest['modes'][mode]['hashes'])
                       for suffix, digest in hashes.items()}
    assert all(sha(Path(path)) == digest for path, digest in original_hashes.items())

    def read(suffix):
        with (original / f'{mode}_0.{suffix}').open() as stream:
            reader = csv.DictReader(stream)
            return reader.fieldnames, list(reader)

    pending_fields, pending = read('pending_nets.csv')
    feedback_fields, feedback = read('critical_feedback.csv')
    input_fields, inputs = read('timing_iteration_0.input.csv')
    _, first_outputs = read('timing_iteration_0.output.csv')
    after = {int(r['task_id']): int(r['criticality_q']) for r in first_outputs}
    crossing = next(r for r in inputs if int(r['criticality_q']) < 64880 <= after[int(r['task_id'])])
    trial_fields, trials = read('net_trials.csv')
    seed_fields, seeds = read('net_trial_seeds.csv')
    step_fields, steps = read('net_trial_steps.csv')
    audit_fields, epoch_audits = read('audit.csv')
    assert trials and steps and seeds
    original_resources = list(struct.iter_unpack('<HHHHII', (original / f'{mode}_0.resources').read_bytes()))
    costs = list(struct.iter_unpack('<QQ', (original / f'{mode}_0.costs').read_bytes()))
    tools = variant / 'mutation_tools'
    root_tool = tools / 'audit_rr_experiments.py'
    path_tool = tools / 'audit_rr_net_trial_paths.py'
    version_tool = tools / 'audit_rr_net_trial_versions.py'
    specs = [('pristine', 'pass'), ('pending_reason', 'path'), ('duplicate_pending', 'path'),
             ('criticality_input', 'path'), ('feedback_without_history', 'path'),
             ('private_acceptance', 'path'), ('private_seed_cost', 'path'),
             ('private_backend_hash', 'version'), ('private_owner_hash', 'version'),
             ('private_final_hash', 'version'), ('final_authority_version', 'version')]
    cases = []
    for name, expected in specs:
        case = output / name
        case.mkdir()
        for child in original.iterdir():
            if child.name != 'pair.json':
                (case / child.name).symlink_to(child, target_is_directory=child.is_dir())
        data = json.loads(json.dumps(manifest))

        def write_csv(suffix, fields, rows):
            for repeat in range(5):
                path = case / f'{mode}_{repeat}.{suffix}'
                assert path.is_symlink()
                path.unlink()
                with path.open('w') as stream:
                    writer = csv.DictWriter(stream, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(rows)
                if suffix in data['modes'][mode]['hashes'][repeat]:
                    data['modes'][mode]['hashes'][repeat][suffix] = sha(path)

        if name == 'pending_reason':
            rows = [dict(r) for r in pending]
            rows[0]['reasons'] = '8'
            write_csv('pending_nets.csv', pending_fields, rows)
        elif name == 'duplicate_pending':
            write_csv('pending_nets.csv', pending_fields, [dict(pending[0]), *pending])
        elif name == 'criticality_input':
            rows = [dict(r) for r in inputs]
            rows[0]['criticality_q'] = str(int(rows[0]['criticality_q']) + 1)
            write_csv('timing_iteration_0.input.csv', input_fields, rows)
        elif name == 'feedback_without_history':
            row = dict(iteration=0, net_id=crossing['net_id'], task_id=crossing['task_id'],
                       old_q=crossing['criticality_q'], new_q=64880, decision=0)
            rows = [row, *feedback]
            write_csv('critical_feedback.csv', feedback_fields, rows)
            for repeat in range(5):
                path = case / f'{mode}_{repeat}.json'
                actual = json.loads(path.read_text())
                path.unlink()
                actual['critical_feedback_events'] = len(rows)
                path.write_text(json.dumps(actual, indent=2) + '\n')
                data['modes'][mode]['runs'][repeat]['critical_feedback_events'] = len(rows)
        elif name in ('private_acceptance', 'private_final_hash'):
            rows = [dict(r) for r in trials]
            key = 'accepted' if name == 'private_acceptance' else 'private_hash'
            rows[0][key] = str(int(rows[0][key]) ^ 1)
            write_csv('net_trials.csv', trial_fields, rows)
        elif name == 'private_seed_cost':
            rows = [dict(r) for r in seeds]
            rows[0]['cost_q'] = str(int(rows[0]['cost_q']) + 1)
            write_csv('net_trial_seeds.csv', seed_fields, rows)
        elif name in ('private_backend_hash', 'private_owner_hash'):
            rows = [dict(r) for r in steps]
            key = 'backend_hash' if name == 'private_backend_hash' else 'owner_hash'
            rows[0][key] = str(int(rows[0][key]) ^ 1)
            write_csv('net_trial_steps.csv', step_fields, rows)
        elif name == 'final_authority_version':
            resources = [list(r) for r in original_resources]
            node = next(i for i, row in enumerate(resources) if row[4] < 0xfffffffe)
            resources[node][4] += 1
            resource_hash = fnv_words(value for row, cost in zip(resources, costs)
                                      for value in (row[0], row[1], cost[0], cost[1], row[4], row[5]))
            for repeat in range(5):
                path = case / f'{mode}_{repeat}.resources'
                path.unlink()
                path.write_bytes(b''.join(struct.pack('<HHHHII', *row) for row in resources))
                data['modes'][mode]['hashes'][repeat]['resources'] = sha(path)
            rows = [dict(r) for r in epoch_audits]
            rows[-1]['resource_hash'] = str(resource_hash)
            write_csv('audit.csv', audit_fields, rows)
        pair = case / 'pair.json'
        pair.write_text(json.dumps(data, indent=2) + '\n')

        def run(label, command):
            with (case / (label + '.log')).open('w') as log:
                return subprocess.run(command, stdout=log, stderr=subprocess.STDOUT).returncode

        rc = run('root', ['python3', str(root_tool), str(pair), '--output', str(case / 'root.json')])
        assert rc == 0, (name, 'Generic hash/counter checks must pass')
        path_proof = case / 'paths.json'
        path_rc = run('paths', ['python3', str(path_tool), str(pair), '--output', str(path_proof)])
        if expected == 'path':
            assert path_rc != 0 and not path_proof.exists() and 'AssertionError' in (case / 'paths.log').read_text()
            version_rc = None
        else:
            assert path_rc == 0 and path_proof.exists(), (name, 'Path audit must pass before version challenge')
            version_proof = case / 'versions.json'
            version_rc = run('versions', ['python3', str(version_tool), str(pair), str(path_proof),
                                         '--output', str(version_proof)])
            if expected == 'version':
                assert version_rc != 0 and not version_proof.exists() and 'AssertionError' in (case / 'versions.log').read_text()
            else:
                assert version_rc == 0 and version_proof.exists()
        cases.append(dict(name=name, expected=expected, generic_checks_passed=True,
                          path_returncode=path_rc, version_returncode=version_rc,
                          manifest_sha256=sha(pair)))
    assert all(sha(Path(path)) == digest for path, digest in original_hashes.items())
    sources = [Path(__file__), original / 'pair.json', root_tool, path_tool, version_tool,
               tools / 'rr_net_trial_replay.py', tools / 'rr_resource_version_replay.py']
    report = dict(status='pristine_and_ten_consistently_rehashed_net_trial_corruptions_checked',
                  cases=cases, original_outputs_unchanged=True,
                  source_sha256={str(p): sha(p) for p in sources},
                  scope='Copied/symlinked completed safeguarded-arm fixtures. All five fixture repetitions '
                        'changed consistently with recorded hashes/counters refreshed. Generic checks pass; '
                        'path or resource-version replay must reject at the intended evidence layer. '
                        'Not additional empirical runs, quality benefit, a search-work oracle or hardware proof.',
                  board_result=False, research_complete=False)
    (output / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(status=report['status'], cases=len(cases))))


if __name__ == '__main__':
    main()
