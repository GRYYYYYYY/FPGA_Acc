"""Challenge completed native ordinary-schedule traces with consistently rehashed fixtures."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pair', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--tools', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    pair, output, tools = args.pair.resolve(), args.output.resolve(), args.tools.resolve()
    original = pair.parent
    manifest = json.loads(pair.read_text())
    assert manifest['status'] == 'completed'
    mode, = manifest['modes']
    assert len(manifest['modes'][mode]['hashes']) == 5
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    original_hashes = {original / f'{mode}_{i}.{suffix}': digest
                       for i, hashes in enumerate(manifest['modes'][mode]['hashes'])
                       for suffix, digest in hashes.items()}
    assert all(sha(p) == h for p, h in original_hashes.items())
    output.mkdir(exist_ok=False)
    cases = []
    specs = [('pristine', None, None),
             ('ripup_dispatch', 'ordinary_ripups.csv', 'dispatch_batch'),
             ('ripup_phase', 'ordinary_ripups.csv', 'phase'),
             ('incumbent_nodes', 'ordinary_ripups.csv', 'tree_nodes_before'),
             ('incumbent_connections', 'ordinary_ripups.csv', 'routed_connections_before'),
             ('effective_width', 'audit.csv', 'issue_width'),
             ('epoch_resource_version_hash', 'audit.csv', 'resource_hash'),
             ('epoch_route_hash', 'audit.csv', 'route_hash'),
             ('pending_reason', 'pending_nets.csv', 'reasons'),
             ('duplicate_ripup', 'ordinary_ripups.csv', None)]
    for name, suffix, field in specs:
        case = output / name
        case.mkdir()
        for child in original.iterdir():
            if child.name != 'pair.json':
                (case / child.name).symlink_to(child, target_is_directory=child.is_dir())
        data = json.loads(json.dumps(manifest))
        if suffix:
            with (original / f'{mode}_0.{suffix}').open() as stream:
                reader = csv.DictReader(stream)
                fields, rows = reader.fieldnames, list(reader)
            assert rows, (name, 'This challenge requires a nonempty native trace')
            if name == 'duplicate_ripup':
                rows.insert(1, dict(rows[0]))
            else:
                rows[0][field] = str(int(rows[0][field]) + 1)
            for repeat in range(5):
                path = case / f'{mode}_{repeat}.{suffix}'
                path.unlink()
                with path.open('w') as stream:
                    writer = csv.DictWriter(stream, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(rows)
                data['modes'][mode]['hashes'][repeat][suffix] = sha(path)
        fixture = case / 'pair.json'
        fixture.write_text(json.dumps(data, indent=2) + '\n')
        results = {}
        for label, script in [('generic', 'audit_rr_experiments.py'),
                              ('schedule', 'audit_rr_ordinary_schedule.py')]:
            proof = case / f'{label}.json'
            with (case / f'{label}.log').open('w') as log:
                result = subprocess.run(['python3', str(tools / script), str(fixture),
                                         '--output', str(proof)], stdout=log, stderr=subprocess.STDOUT)
            results[label] = result.returncode
            if label == 'generic' or name == 'pristine':
                assert result.returncode == 0 and proof.exists(), (name, label)
            else:
                assert result.returncode != 0 and not proof.exists(), (name, label)
                assert 'AssertionError' in (case / f'{label}.log').read_text(), name
        cases.append(dict(name=name, returncodes=results, fixture_sha256=sha(fixture)))
    assert all(sha(p) == h for p, h in original_hashes.items())
    sources = [Path(__file__).resolve(), pair, *tools.glob('*.py')]
    report = dict(status='pristine_and_nine_consistently_rehashed_schedule_corruptions_checked',
                  cases=cases, original_outputs_unchanged=True,
                  source_sha256={str(p): sha(p) for p in sources},
                  scope='Copied native five-repeat fixtures; all edited repetitions and manifest hashes '
                        'agree. Generic checks must pass; independent schedule/version replay must reject '
                        'semantic corruptions. Not additional routing runs, quality acceptance, an '
                        'independent search-work oracle or physical hardware evidence.',
                  board_result=False, research_complete=False)
    (output / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(status=report['status'], cases=len(cases))))


if __name__ == '__main__':
    main()
