"""Independently rebuild the fixed-other-net necessary occupied frontier."""
import collections
import csv
import hashlib
import heapq
import json
import struct
from pathlib import Path

R = Path(__file__).resolve().parents[1]
B = R / 'work/sb3_ex5p_capacity_delay_bound_20261015'
F = R / 'work/sb3_ex5p_delay_frontier_20261015'
INF = (1 << 64) - 1

def main():
    hashes = {}
    def load(path):
        path = Path(path)
        data = path.read_bytes()
        hashes[str(path)] = hashlib.sha256(data).hexdigest()
        return data
    report = json.loads(load(F / 'independent_audit.json'))
    certificate = json.loads(load(B / 'certificate_audit.json'))
    for document in [report, certificate]:
        for path, expected in document['source_sha256'].items():
            load(path)
            assert hashes[str(Path(path))] == expected, path
    protocol = json.loads(load(R / 'work/sb3_fixed_feedback_pair_20261015/protocol.json'))
    case = next(row for row in protocol['cases'] if row['label'] == 'ex5p')
    prefix = case['input_prefix']
    nodes = list(struct.iter_unpack('<IHH', load(prefix + '.nodes')))
    edges = list(struct.iter_unpack('<IHH', load(prefix + '.edges')))
    reverse = [[] for _ in nodes]
    for u, (start, count, _) in enumerate(nodes):
        for v, _, weight in edges[start:start + count]:
            reverse[v].append((u, weight))
    def shortest(adjacency, source):
        distances = [INF] * len(nodes)
        distances[source] = 0
        pending = [(0, source)]
        while pending:
            value, u = heapq.heappop(pending)
            if value != distances[u]:
                continue
            for v, weight in adjacency[u]:
                candidate = value + weight
                if candidate < distances[v]:
                    distances[v] = candidate
                    heapq.heappush(pending, (candidate, v))
        return distances
    suffix = shortest(reverse, 14256)
    outcomes = []
    for arm in report['outcomes']:
        label = arm['arm']
        directory = R / 'work/sb3_fixed_feedback_pair_20261015/native_runs' / ('ex5p_' + label + '_0')
        owner_sets = collections.defaultdict(set)
        tree_text = load(directory / 'route.route_trees.csv').decode()
        all_nets = set()
        for row in csv.DictReader(tree_text.splitlines()):
            net = int(row['net_id'])
            all_nets.add(net)
            if net == 138:
                continue
            for key in ['parent', 'child']:
                if row[key] != row['source']:
                    owner_sets[int(row[key])].add(net)
        assert len(all_nets - {138}) == 612
        resources = list(struct.iter_unpack('<HHHHII', load(directory / 'route.resources')))
        assert len(resources) == len(nodes)
        allowed = [len(owner_sets[v]) < row[1] for v, row in enumerate(resources)]
        adjacency = [[] for _ in nodes]
        for u, (start, count, _) in enumerate(nodes):
            if allowed[u]:
                adjacency[u] = [(v, w) for v, _, w in edges[start:start + count] if allowed[v]]
        forward = shortest(adjacency, 43804)
        archived = [v[0] for v in struct.iter_unpack('<Q', load(B / (label + '.distances.u64')))]
        assert forward == archived, label
        expected = collections.defaultdict(list)
        examined = 0
        for u, (start, count, _) in enumerate(nodes):
            if forward[u] == INF:
                continue
            for v, _, w in edges[start:start + count]:
                examined += 1
                if not allowed[v] and suffix[v] != INF and forward[u] + w + suffix[v] <= 567:
                    expected[v].append(dict(source=u, edge_delay_ps=w,
                                            optimistic_total_ps=forward[u] + w + suffix[v]))
        recorded = {row['node']: row for row in arm['frontier']}
        assert set(expected) == set(recorded)
        for node, incoming in expected.items():
            actual = recorded[node]
            assert actual['capacity'] == resources[node][1]
            assert actual['incoming_edges'] == incoming
            assert [v['id'] for v in actual['other_owners']] == sorted(owner_sets[node])
        union = set().union(*(owner_sets[v] for v in expected))
        assert len(expected) == arm['frontier_node_count']
        assert len(union) == arm['competing_net_count']
        assert arm['baseline_first_blocked_node'] in expected
        outcomes.append(dict(arm=label, frontier_nodes=len(expected), competing_nets=len(union),
                             candidate_edges_examined=examined, all_forward_distances_match=True))
    load(Path(__file__).resolve())
    output = dict(status='both_frontiers_independently_rebuilt_exact_nodes_owners_and_edges_match',
                  outcomes=outcomes, source_sha256=hashes, adopted=False, research_complete=False,
                  scope='Fixed-other612net packed-delay necessary frontier only; no sufficient release set, global CPD, routing-policy or board claim.')
    destination = F / 'frontier_rebuild_audit.json'
    with destination.open('x') as stream:
        json.dump(output, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=output['status'], outcomes=outcomes)))

if __name__ == '__main__':
    main()
