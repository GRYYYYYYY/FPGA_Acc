"""Match actual host fixture private/public resource hashes with an independent model."""
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path
import rr_resource_version_replay
from rr_resource_version_replay import ResourceVersions, replay_private_versions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixtures', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    files = [Path(__file__).resolve(), Path(rr_resource_version_replay.__file__).resolve()]
    proof = json.loads((args.fixtures / 'audit.json').read_text())
    files.append(args.fixtures / 'audit.json')
    for path, digest in proof['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    cases = []
    for label in ('accepted', 'rejected'):
        tables = {}
        for suffix in ('net_trials', 'net_trial_steps', 'net_trial_branches'):
            path = args.fixtures / ('trial_' + label + '.' + suffix + '.csv')
            files.append(path)
            with path.open() as stream:
                tables[suffix] = [{k: int(v) for k, v in r.items()} for r in csv.DictReader(stream)]
        trial, = tables['net_trials']
        count = 6 if label == 'accepted' else 7
        model = ResourceVersions([(0, 1, 256, 0, 0, 0xffffffff) for _ in range(count)])
        roots = {7: 0, 8: 4} if label == 'accepted' else {7: 0}
        task_net = {0: 7, 1: 8} if label == 'accepted' else {0: 7, 1: 7}
        trees, paths = {net: {root: None} for net, root in roots.items()}, {}
        model.update_cost(256, 0)
        for iteration in range(3):
            if iteration:
                dirty = set()
                for net, tree in trees.items():
                    for node, parent in tree.items():
                        if parent is not None:
                            model.owners[node].remove(net)
                            dirty.add(node)
                trees = {net: {root: None} for net, root in roots.items()}
                paths = {}
                model.refresh(dirty)
            branch0 = [2, 3] if iteration == 1 else [1, 3]
            branch1 = ([5] if label == 'accepted' else [4, 6] if iteration == 0 else [5, 6])
            # The rejected fixture's second task leads the third ordinary epoch.
            order = [1, 0] if label == 'rejected' and iteration == 2 else [0, 1]
            for task in order:
                net = task_net[task]
                branch = branch0 if task == 0 else branch1
                model.backend_commit(branch, net)
                parent = roots[net]
                for node in branch:
                    assert node not in trees[net]
                    trees[net][node] = parent
                    model.owners[node].add(net)
                    parent = node
                paths[task] = list(branch)
                model.refresh(branch)
            model.update_cost(256, 256)
        # This is a reconstruction from the known ordinary fixture schedule,
        # not initialization from the private trace's own claimed version bytes.
        assert model.resource_hash() == trial['before_hash']
        original = copy.deepcopy(model.state)
        net_tasks = {task for task, net in task_net.items() if net == 7}
        result, result_trees, result_paths, increments = replay_private_versions(
            model, trial, tables, trees, paths, 0, net_tasks, [0, 1])
        assert result.resource_hash() == trial['after_hash']
        assert model.state == original, 'Private replay mutated its input authority'
        assert bool(trial['accepted']) == (result is not model)
        cases.append(dict(name=label + '_pristine', passed=True, private_version_increments=increments))
        for mutation in ('before_hash', 'ripup_hash', 'backend_hash', 'owner_hash',
                         'private_hash', 'after_hash', 'after_route_hash'):
            row, bad = copy.deepcopy(trial), copy.deepcopy(tables)
            if mutation in ('backend_hash', 'owner_hash'):
                bad['net_trial_steps'][0][mutation] ^= 1
            else:
                row[mutation] ^= 1
            try:
                replay_private_versions(model, row, bad, trees, paths, 0, net_tasks, [0, 1])
            except AssertionError:
                cases.append(dict(name=label + '_' + mutation, rejected=True))
            else:
                raise AssertionError('Incorrect resource hash passed: ' + mutation)
            assert model.state == original
    report = dict(status='component_private_and_published_version_hashes_replayed', cases=cases,
                  source_sha256={str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  scope='Two actual host-writer fixtures: ordinary history reconstructed, then private '
                        'ripup/backend/owner/final/publication hashes matched. Fourteen in-memory '
                        'hash corruptions rejected. No native five-repeat integration, per-CU read-version '
                        'receipts, hardware atomicity or independent search-work oracle.',
                  board_result=False, research_complete=False)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(status=report['status'], cases=len(cases))))


if __name__ == '__main__':
    main()
