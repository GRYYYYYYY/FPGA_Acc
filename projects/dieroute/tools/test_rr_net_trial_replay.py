"""Check independent path/predicate replay on actual host-writer component fixtures."""
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path
from rr_net_trial_replay import replay_trial
import rr_net_trial_replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixtures', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    fixtures = args.fixtures.resolve()
    proof = json.loads((fixtures / 'audit.json').read_text())
    assert proof['status'] == 'actual_host_trial_trace_writer_accept_and_reject_fixture_checked'
    for path, digest in proof['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    files = [Path(__file__).resolve(), Path(rr_net_trial_replay.__file__).resolve(), fixtures / 'audit.json']
    cases = []
    for label in ('accepted', 'rejected'):
        tables = {}
        for suffix in ('net_trials', 'net_trial_steps', 'net_trial_seeds', 'net_trial_branches',
                       'net_trial_connections', 'net_trial_paths'):
            path = fixtures / ('trial_' + label + '.' + suffix + '.csv')
            files.append(path)
            with path.open() as stream:
                tables[suffix] = [{k: int(v) for k, v in r.items()} for r in csv.DictReader(stream)]
        trial, = tables['net_trials']
        before = [r for r in tables['net_trial_connections'] if r['stage'] == 0]
        tasks = {r['task_id']: {k: r[k] for k in ('net_id', 'source', 'sink', 'max_hops', 'priority', 'reserved')}
                 for r in before}
        q = {r['task_id']: r['criticality_q'] for r in before}
        if label == 'accepted':
            nodes = [(0, 2, 0), (2, 1, 1), (3, 1, 1), (4, 0, 0), (4, 1, 0), (5, 0, 0)]
            edges = [(1, 1, 100), (2, 20, 1), (3, 1, 1), (3, 20, 1), (5, 3, 1)]
            trees = {7: {0: None, 1: 0, 3: 1}, 8: {4: None, 5: 4}}
            paths = {0: [1, 3], 1: [5]}
            tasks[1] = dict(net_id=8, source=4, sink=5, max_hops=16, priority=1, reserved=0)
            q[1] = 0
        else:
            nodes = [(0, 4, 0), (4, 1, 1), (5, 1, 1), (6, 0, 0), (6, 1, 1), (7, 1, 1), (8, 0, 0)]
            edges = [(1, 1, 100), (2, 20, 1), (4, 1, 100), (5, 20, 1),
                     (3, 1, 1), (3, 20, 1), (6, 1, 1), (6, 20, 1)]
            trees = {7: {0: None, 1: 0, 3: 1, 5: 0, 6: 5}}
            paths = {0: [1, 3], 1: [5, 6]}
        initial = [(0, 1, 256, 0, 0, 0xffffffff) for _ in nodes]
        result = replay_trial(trial, tables, nodes, edges, initial, trees, paths, tasks, q)
        assert result['accepted'] == (label == 'accepted')
        assert not result['version_replay_verified']
        cases.append(dict(name=label + '_pristine', passed=True, expanded=result['expanded']))
        for corruption in ('acceptance_bit', 'seed_cost', 'declared_delay', 'truncated_success_without_failure'):
            bad_trial, bad = copy.deepcopy(trial), copy.deepcopy(tables)
            if corruption == 'acceptance_bit':
                bad_trial['accepted'] ^= 1
            elif corruption == 'seed_cost':
                bad['net_trial_seeds'][0]['cost_q'] += 1
            elif corruption == 'declared_delay':
                bad['net_trial_connections'][0]['delay_ps'] += 1
            else:
                bad_trial['steps'] -= 1
                bad['net_trial_steps'].pop()
            try:
                replay_trial(bad_trial, bad, nodes, edges, initial, trees, paths, tasks, q)
            except AssertionError as error:
                if corruption == 'truncated_success_without_failure':assert str(error) == 'Truncated trial omits failed step'
                cases.append(dict(name=label + '_' + corruption, rejected=True))
            else:
                raise AssertionError('Corrupted fixture passed: ' + corruption)
    report = dict(status='component_host_trace_private_paths_and_predicates_replayed', cases=cases,
                  source_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  scope='Actual accepted/rejected host-writer fixtures with explicit small graph/incumbent contexts. '
                        'Submitted seeds, paths, local delays, wire/capacity/acceptance predicates and logical '
                        'publication replayed; eight in-memory corruptions rejected. Not five new routing runs, '
                        'whole-experiment pending replay or independent resource-version/hash reconstruction.',
                  board_result=False, research_complete=False)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(status=report['status'], cases=len(cases))))


if __name__ == '__main__':
    main()
