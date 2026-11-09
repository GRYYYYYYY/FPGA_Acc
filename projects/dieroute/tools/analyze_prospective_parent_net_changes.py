"""Describe per-net changes in reviewed parents without changing routing policy."""
import array
import collections
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    evidence, output = (Path(v).resolve() for v in sys.argv[1:])
    output.mkdir()
    report = json.loads(evidence.read_text())
    assert report['status'] == 'partial_prospective_parent_stage_quality_independently_joined'
    refs = {}

    def sha(path):
        path = Path(path)
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                h.update(block)
        refs[str(path.resolve())] = h.hexdigest()
        return h.hexdigest()

    for name, expected in report['source_sha256'].items():
        assert sha(name) == expected, name
    cases = []
    for row in report['rows']:
        label = row['label']
        rt = root / 'work/prospective_apex2_seeds6_10_roundtrip_20261020' / label
        parent = root / 'work/prospective_apex2_seeds6_10_parents_v2_20261020/parents' / label
        base = root / 'work/prospective_apex2_seeds6_10_baselines_20261020' / label
        cases.append((row, rt, parent, base))
    assert cases
    graph_hash = sha(cases[0][3] / 'rr_graph.xml')
    command = [sys.executable, str(root / 'tools/export_vpr_wirelength_weights.py'),
               str(cases[0][3] / 'rr_graph.xml'), str(cases[0][1] / 'input.nodes'), str(output / 'weights')]
    for _, _, parent, base in cases:
        assert sha(base / 'rr_graph.xml') == graph_hash
        command += ['--case', str(parent / 'route.route_trees.csv'), str(parent / 'native_validation/validation.json')]
    with (output / 'weight_export.log').open('x') as stream:
        subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)
    weights = array.array('H')
    weights.frombytes((output / 'weights/node_wirelength.u16').read_bytes())
    if sys.byteorder != 'little':
        weights.byteswap()
    outcomes = []
    for row, rt, parent, base in cases:
        dies = array.array('H')
        dies.frombytes((rt / 'topology.node_die').read_bytes())
        if sys.byteorder != 'little':
            dies.byteswap()

        def inventory(path):
            nodes, edges = collections.defaultdict(set), collections.defaultdict(set)
            with path.open() as stream:
                for record in csv.DictReader(stream):
                    n, source, u, v = (int(record[k]) for k in ['net_id', 'source', 'parent', 'child'])
                    nodes[n].update([source, u, v])
                    edges[n].add((u, v))
            sha(path)
            return {n: (sum(weights[v] for v in members),
                        sum(dies[u] != dies[v] for u, v in edges[n])) for n, members in nodes.items()}

        before = inventory(rt / 'native_tree.csv')
        after = inventory(parent / 'route.route_trees.csv')
        assert before.keys() == after.keys()
        fanout = collections.Counter()
        with (rt / 'connections.csv').open() as stream:
            for record in csv.DictReader(stream):
                fanout[int(record['net_id'])] += 1
        assert fanout.keys() == before.keys()
        net_rows = [{'net_id': n, 'fanout': fanout[n], 'baseline_wirelength': before[n][0],
                     'candidate_wirelength': after[n][0], 'wirelength_delta': after[n][0] - before[n][0],
                     'baseline_crossings': before[n][1], 'candidate_crossings': after[n][1],
                     'crossing_delta': after[n][1] - before[n][1]} for n in sorted(before)]
        assert sum(v[0] for v in before.values()) == row['baseline_wirelength']
        assert sum(v[0] for v in after.values()) == row['wirelength']
        assert sum(v[1] for v in before.values()) == row['baseline_modeled_transitions']
        assert sum(v[1] for v in after.values()) == row['modeled_transitions']
        path = output / (row['label'] + '_nets.csv')
        with path.open('x') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(net_rows[0]))
            writer.writeheader()
            writer.writerows(net_rows)
        groups = []
        for label, lo, hi in [('1to3', 1, 3), ('4to15', 4, 15), ('16plus', 16, 10**9)]:
            selected = [v for v in net_rows if lo <= v['fanout'] <= hi]
            groups.append({'fanout': label, 'nets': len(selected),
                           'wirelength_delta': sum(v['wirelength_delta'] for v in selected),
                           'crossing_delta': sum(v['crossing_delta'] for v in selected)})
        outcomes.append({'label': row['label'], 'nets': len(net_rows), 'groups': groups,
                         'nets_with_increased_wirelength': sum(v['wirelength_delta'] > 0 for v in net_rows),
                         'nets_with_decreased_wirelength': sum(v['wirelength_delta'] < 0 for v in net_rows),
                         'nets_with_fewer_crossings_but_more_wirelength': sum(v['crossing_delta'] < 0 and v['wirelength_delta'] > 0 for v in net_rows)})
        for path in [path, rt / 'connections.csv', rt / 'topology.node_die']:
            sha(path)
    for path in [evidence, output / 'weights/audit.json', Path(__file__).resolve()]:
        sha(path)
    result = {'status': 'reviewed_parent_per_net_wirelength_and_crossing_changes_reconciled',
              'outcomes': outcomes, 'source_sha256': refs, 'research_complete': False,
              'scope': 'Descriptive accounting on interim parents; per-net wirelength sums match native totals and crossings match audited totals. No causal attribution of CPD, new ablation, policy tuning or final prospective outcome.'}
    (output / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(outcomes))


if __name__ == '__main__':
    main()
