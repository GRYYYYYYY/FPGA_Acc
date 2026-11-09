"""Compare exact critical paths and shared prefixes, without inferring RC cause."""
import array
import collections
import csv
import hashlib
import json
from pathlib import Path
import struct
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    diagnosis = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    evidence = json.loads(diagnosis.read_text())
    refs = {}

    def sha(path):
        path = Path(path)
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        refs[str(path.resolve())] = h
        return h

    for name, expected in evidence['source_sha256'].items():
        assert sha(name) == expected, name
    weights_path = root / 'work/prospective_parent_net_changes_20261020/weights/node_wirelength.u16'
    weights = array.array('H')
    weights.frombytes(weights_path.read_bytes())
    if sys.byteorder != 'little':
        weights.byteswap()
    results = []
    for case in evidence['rows']:
        label = case['label']
        rt = root / 'work/prospective_apex2_seeds6_10_roundtrip_20261020' / label
        costs = root / 'work/prospective_apex2_seeds6_10_native_costs_20261020' / label
        nodes = list(struct.iter_unpack('<IHH', (costs / 'input.nodes').read_bytes()))
        edges = list(struct.iter_unpack('<IHH', (costs / 'input.edges').read_bytes()))
        with (rt / 'connections.csv').open() as stream:
            tasks = {int(v['id']): {k: int(v[k]) for k in ['net_id', 'source', 'sink']}
                     for v in csv.DictReader(stream)}
        measured = {}
        for mode, tree in [('baseline', rt / 'native_tree.csv'),
                           ('parent', root / 'work/prospective_apex2_seeds6_10_parents_v2_20261020/parents' / label / 'route.route_trees.csv')]:
            parents = collections.defaultdict(dict)
            with tree.open() as stream:
                for row in csv.DictReader(stream):
                    net, child, parent = (int(row[k]) for k in ['net_id', 'child', 'parent'])
                    assert child not in parents[net]
                    parents[net][child] = parent

            def path(task):
                v, source, net = task['sink'], task['source'], task['net_id']
                reverse, seen = [v], {v}
                while v != source:
                    v = parents[net][v]
                    assert v not in seen
                    seen.add(v)
                    reverse.append(v)
                return list(reversed(reverse))

            measured[mode] = {}
            for selected in case['selected_critical_regressions']:
                task = selected['task']
                target = tasks[task]
                route = path(target)
                sink_paths = {t['sink']: path(t) for t in tasks.values() if t['net_id'] == target['net_id']}
                usage = collections.Counter(v for p in sink_paths.values() for v in p)
                delays = []
                for u, v in zip(route, route[1:]):
                    begin, count, _ = nodes[u]
                    matches = [d for dst, _, d in edges[begin:begin + count] if dst == v]
                    assert matches
                    delays.append(min(matches))
                shared_prefix = []
                for v in route[1:]:
                    if usage[v] < 2:
                        break
                    shared_prefix.append(v)
                tree_members = set(parents[target['net_id']]) | {target['source']}
                measured[mode][task] = {'path': route, 'path_edges': len(route) - 1,
                                        'path_wirelength': sum(weights[v] for v in route),
                                        'additive_input_edge_delay_ps': sum(delays),
                                        'shared_prefix_nodes': len(shared_prefix),
                                        'shared_prefix_wirelength': sum(weights[v] for v in shared_prefix),
                                        'off_path_tree_wirelength': sum(weights[v] for v in tree_members - set(route))}
            sha(tree)
        for selected in case['selected_critical_regressions']:
            task = selected['task']
            before, after = measured['baseline'][task], measured['parent'][task]
            results.append({'label': label, **selected, 'baseline': before, 'parent': after,
                            'path_identical': before['path'] == after['path']})
        for path in [rt / 'connections.csv', costs / 'input.nodes', costs / 'input.edges']:
            sha(path)
    for path in [diagnosis, weights_path, Path(__file__).resolve()]:
        sha(path)
    result = {'status': 'prospective_critical_paths_and_shared_prefixes_reconstructed', 'rows': results,
              'source_sha256': refs, 'research_complete': False,
              'scope': 'Exact final rooted paths, channel spans, additive input edge delays and distinct-sink shared prefixes. Off-path span is not capacitance. No historical attachment inference, calibrated RC decomposition or causal delay attribution; prospective policy unchanged.'}
    with output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps([{k: v for k, v in row.items() if k not in ['baseline', 'parent']} |
                      {'baseline': {k: v for k, v in row['baseline'].items() if k != 'path'},
                       'parent': {k: v for k, v in row['parent'].items() if k != 'path'}} for row in results]))


if __name__ == '__main__':
    main()
