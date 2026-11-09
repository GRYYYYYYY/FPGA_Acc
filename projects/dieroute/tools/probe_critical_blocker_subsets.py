"""Exhaust recorded baseline-path blocker subsets in a relaxed path problem."""
import collections
import csv
import hashlib
import heapq
import itertools
import json
from pathlib import Path
import struct
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    directory, output = (Path(v).resolve() for v in sys.argv[1:])
    refs = {}

    def read(path):
        path = Path(path)
        refs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text())

    blockers = read(directory / 'baseline_path_blockers.json')
    profile = read(directory / 'path_profile.json')
    prior = read(directory / 'capacity_delay_floors.json')
    for evidence in [blockers, profile, prior]:
        for name, expected in evidence['source_sha256'].items():
            actual = hashlib.sha256(Path(name).read_bytes()).hexdigest()
            assert actual == expected, name
            refs[name] = actual
    targets = {(r['label'], r['task']): r for r in profile['rows']}
    floors = {(r['label'], r['task']): r for r in prior['rows']}
    cases = collections.defaultdict(list)
    for row in blockers['rows']:
        cases[row['label']].append(row)
    results = []
    for label, rows in cases.items():
        cost = root / 'work/prospective_apex2_seeds6_10_native_costs_20261020' / label
        nodes = list(struct.iter_unpack('<IHH', (cost / 'input.nodes').read_bytes()))
        edges = list(struct.iter_unpack('<IHH', (cost / 'input.edges').read_bytes()))
        resources = list(struct.iter_unpack('<HHHHII', (cost / 'input.resources').read_bytes()))
        tree = root / 'work/prospective_apex2_seeds6_10_parents_v2_20261020/parents' / label / 'route.route_trees.csv'
        owners = collections.defaultdict(set)
        with tree.open() as stream:
            for row in csv.DictReader(stream):
                for name in ['source', 'parent', 'child']:
                    owners[int(row[name])].add(int(row['net_id']))
        for row in rows:
            target = targets[label, row['task']]
            source, sink = target['baseline']['path'][0], target['baseline']['path'][-1]
            outcomes = []
            recorded = row['blocking_nets']
            assert len(recorded) <= 3
            for size in range(len(recorded) + 1):
                for subset in itertools.combinations(recorded, size):
                    removed = {row['net_id'], *subset}
                    allowed = [len(owners.get(v, set()) - removed) < r[1] for v, r in enumerate(resources)]
                    assert allowed[source] and allowed[sink]
                    distance, parent, queue = {source: 0}, {}, [(0, source)]
                    while queue:
                        delay, u = heapq.heappop(queue)
                        if distance[u] != delay:
                            continue
                        if u == sink:
                            break
                        begin, count, _ = nodes[u]
                        for v, _, weight in edges[begin:begin + count]:
                            candidate = delay + weight
                            if allowed[v] and candidate < distance.get(v, 10**30):
                                distance[v], parent[v] = candidate, u
                                heapq.heappush(queue, (candidate, v))
                    assert sink in distance
                    path = [sink]
                    while path[-1] != source:
                        path.append(parent[path[-1]])
                    path.reverse()
                    outcomes.append({'removed_blocker_nets': list(subset), 'minimum_additive_delay_ps': distance[sink],
                                     'meets_baseline_delay': distance[sink] <= target['baseline']['additive_input_edge_delay_ps'],
                                     'path': path})
            assert outcomes[0]['minimum_additive_delay_ps'] == floors[label, row['task']]['minimum_additive_delay_ps']
            assert outcomes[-1]['meets_baseline_delay']
            for a in outcomes:
                for b in outcomes:
                    if set(a['removed_blocker_nets']) <= set(b['removed_blocker_nets']):
                        assert b['minimum_additive_delay_ps'] <= a['minimum_additive_delay_ps']
            eligible = [v for v in outcomes if v['meets_baseline_delay']]
            minimum = min(len(v['removed_blocker_nets']) for v in eligible)
            results.append({'label': label, 'task': row['task'], 'net_id': row['net_id'],
                            'recorded_blockers': recorded, 'outcomes': outcomes,
                            'minimum_removed_within_recorded_set': minimum,
                            'minimum_sufficient_subsets': [v['removed_blocker_nets'] for v in eligible if len(v['removed_blocker_nets']) == minimum]})
    path = Path(__file__).resolve()
    refs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    result = {'status': 'recorded_critical_blocker_subsets_exhaustively_probed', 'rows': results,
              'source_sha256': refs, 'research_complete': False,
              'scope': 'Exhaustive subsets only of recorded blockers on baseline paths, under root-inclusive capacity. Selected net and blockers removed without rebuilding them; one unconstrained connection. Not minimum global blocker set, legal whole-net exchange, native timing improvement or an adopted route. Frozen policy unchanged.'}
    with output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps([{k: v for k, v in row.items() if k != 'outcomes'} for row in results]))


if __name__ == '__main__':
    main()
