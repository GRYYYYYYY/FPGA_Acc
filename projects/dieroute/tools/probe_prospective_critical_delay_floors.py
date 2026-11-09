"""Capacity-aware single-connection lower bounds; never publish candidate routes."""
import collections
import csv
import hashlib
import heapq
import json
from pathlib import Path
import struct
import sys
import time


def main():
    root = Path(__file__).resolve().parents[1]
    profile_path, output = (Path(v).resolve() for v in sys.argv[1:])
    profile = json.loads(profile_path.read_text())
    refs = {}

    def sha(path):
        path = Path(path)
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        refs[str(path.resolve())] = h
        return h

    for name, expected in profile['source_sha256'].items():
        assert sha(name) == expected, name
    groups = collections.defaultdict(list)
    for row in profile['rows']:
        groups[row['label']].append(row)
    results = []
    for label, targets in groups.items():
        costs = root / 'work/prospective_apex2_seeds6_10_native_costs_20261020' / label
        rt = root / 'work/prospective_apex2_seeds6_10_roundtrip_20261020' / label
        tree = root / 'work/prospective_apex2_seeds6_10_parents_v2_20261020/parents' / label / 'route.route_trees.csv'
        nodes = list(struct.iter_unpack('<IHH', (costs / 'input.nodes').read_bytes()))
        edges = list(struct.iter_unpack('<IHH', (costs / 'input.edges').read_bytes()))
        resources = list(struct.iter_unpack('<HHHHII', (costs / 'input.resources').read_bytes()))
        assert len(nodes) == len(resources)
        owners = collections.defaultdict(set)
        with tree.open() as stream:
            for row in csv.DictReader(stream):
                net = int(row['net_id'])
                for key in ['source', 'parent', 'child']:
                    owners[int(row[key])].add(net)
        assert all(len(nets) <= resources[v][1] for v, nets in owners.items())
        with (rt / 'connections.csv').open() as stream:
            tasks = {int(row['id']): row for row in csv.DictReader(stream)}
        for target in targets:
            started = time.monotonic_ns()
            task = tasks[target['task']]
            source, sink, net = (int(task[k]) for k in ['source', 'sink', 'net_id'])
            assert net == target['net_id']
            allowed = [len(owners.get(v, set()) - {net}) < resource[1] for v, resource in enumerate(resources)]
            assert allowed[source] and allowed[sink]
            distances, parents, queue = {source: 0}, {}, [(0, source)]
            expanded = 0
            while queue:
                delay, u = heapq.heappop(queue)
                if delay != distances[u]:
                    continue
                expanded += 1
                if u == sink:
                    break
                begin, count, _ = nodes[u]
                for v, _, weight in edges[begin:begin + count]:
                    candidate = delay + weight
                    if allowed[v] and candidate < distances.get(v, 10**30):
                        distances[v] = candidate
                        parents[v] = u
                        heapq.heappush(queue, (candidate, v))
            assert sink in distances
            path = [sink]
            while path[-1] != source:
                path.append(parents[path[-1]])
            path.reverse()
            assert len(set(path)) == len(path)
            total = 0
            for u, v in zip(path, path[1:]):
                begin, count, _ = nodes[u]
                total += min(weight for dst, _, weight in edges[begin:begin + count] if dst == v)
            assert total == distances[sink] <= target['parent']['additive_input_edge_delay_ps']
            results.append({'label': label, 'task': target['task'], 'net_id': net,
                            'minimum_additive_delay_ps': total,
                            'current_additive_delay_ps': target['parent']['additive_input_edge_delay_ps'],
                            'baseline_additive_delay_ps': target['baseline']['additive_input_edge_delay_ps'],
                            'floor_meets_baseline_delay': total <= target['baseline']['additive_input_edge_delay_ps'],
                            'expanded': expanded, 'wall_ns': time.monotonic_ns() - started, 'path': path})
        for path in [tree, rt / 'connections.csv', *[costs / ('input.' + suffix) for suffix in ['nodes', 'edges', 'resources']]]:
            sha(path)
    for path in [profile_path, Path(__file__).resolve()]:
        sha(path)
    result = {'status': 'capacity_aware_critical_single_connection_delay_floors_computed', 'rows': results,
              'source_sha256': refs, 'research_complete': False,
              'scope': 'Other nets retain exact root-inclusive occupancy; selected whole net removed. Single-connection Dijkstra lower bound only: ignores own-net remaining sinks, crossing and wirelength caps, native RC and complete-tree legality. Paths are not adoptable routes or prospective improvements.'}
    with output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps([{k: v for k, v in row.items() if k != 'path'} for row in results]))


if __name__ == '__main__':
    main()
