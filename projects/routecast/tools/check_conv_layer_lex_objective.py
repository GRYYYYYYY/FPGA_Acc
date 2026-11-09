"""Independently reconstruct lexicographic objectives and single-net occupancy bounds."""
import collections
import json
import shutil
from array import array
from pathlib import Path

from pre_route_endpoints import sha
from prepared_csr import read


def run():
    base = Path('experiments')
    parent = base / 'conv_layer_length_switch_prediction_v2_2026-10-06'
    search = base / 'conv_layer_no_worsening_lex_search_2026-10-06'
    sr = json.loads((search / 'receipt.json').read_text())
    sp = json.loads((search / 'protocol.json').read_text())
    pp = json.loads((parent / 'protocol.json').read_text())
    pr = json.loads((parent / 'receipt.json').read_text())
    assert sr['queries'] == 75
    assert sr['protocol_sha256'] == sha(search / 'protocol.json')
    assert sr['journal_sha256'] == sha(search / 'queries.jsonl')
    assert pr['prediction_sha256'] == sha(parent / 'prediction.json')
    assert pr['protocol_sha256'] == sha(parent / 'protocol.json')
    assert all(sha(p) == h for p, h in sp['inputs_sha256'].items())
    assert all(sha(search / 'source' / n) == h for n, h in sp['source_sha256'].items())
    assert not sp['banned_channel_nodes'] and sp['graph'] == pp['inputs']['graph']
    m, f = read(base / 'conv_layer_length_switch_csr_2026-10-06/csr', sp['graph']['sha256'])
    assert sha(base / 'conv_layer_length_switch_csr_2026-10-06/csr/manifest.json') == pp['csr_manifest_sha256']
    slots = array('Q', [0]) * m['edges']
    for slot, eid in enumerate(f['edge_ids']):
        slots[eid] = slot

    def used(row, edges):
        current = row['source']
        nodes = {current}
        for eid in edges:
            slot = slots[eid]
            assert f['row_offsets'][current] <= slot < f['row_offsets'][current + 1]
            current = f['dest_ranks'][slot]
            assert current not in nodes
            nodes.add(current)
        assert current == row['sink']
        return nodes

    def span(nodes):
        return sum(max(f['xhigh'][n] - f['xlow'][n], f['yhigh'][n] - f['ylow'][n]) + 1
                   for n in nodes if f['types'][n] in (4, 5))

    scale = span(range(m['nodes'])) + 1
    assert scale == sp['lexicographic_span_scale']
    prediction = json.loads((parent / 'prediction.json').read_text())
    original = {r['connection_id']: r for r in prediction['connections']}
    occupancy = {int(n): v for n, v in prediction['node_occupancy'].items()}
    queries = [json.loads(s) for s in (search / 'queries.jsonl').read_text().splitlines()]
    assert len(queries) == len({r['connection_id'] for r in queries}) == 75
    own = collections.defaultdict(set)
    selected = {r['net_id'] for r in queries}
    closure = {r['connection_id'] for r in original.values() if r['net_id'] in selected}
    assert closure == {r['connection_id'] for r in queries}
    for cid in closure:
        r = original[cid]
        own[r['net_id']].update(used(r, r['physical_edge_ids']))
    witnesses = []
    union = collections.defaultdict(set)
    for row in queries:
        old = original[row['connection_id']]
        assert all(row[k] == old[k] for k in ('net_id', 'source', 'sink'))
        result = row['result']
        if result['status'] != 'FOUND':
            assert result['status'] == 'LABEL_LIMIT', 'original path is a feasible witness; unexpected unreachable'
            continue
        candidate = used(row, result['physical_edge_ids'])
        old_nodes = used(old, old['physical_edge_ids'])
        net = row['net_id']

        def units(nodes):
            return sum(max(0, occupancy.get(n, 0) - (n in own[net]) + 1 - f['capacities'][n]) -
                       max(0, occupancy.get(n, 0) - (n in own[net]) - f['capacities'][n])
                       for n in nodes - {row['source']})

        objective = (units(candidate), span(candidate))
        baseline = (units(old_nodes), span(old_nodes))
        assert objective <= baseline
        assert objective == (result['incremental_overflow_units_excluding_constant_source'], result['channel_span'])
        assert result['cost'] == objective[0] * scale + objective[1] and objective[1] < scale
        assert all(max(0, occupancy.get(n, 0) - (n in own[net]) + 1 - f['capacities'][n]) <=
                   max(0, occupancy.get(n, 0) - f['capacities'][n]) for n in candidate)
        union[net].update(candidate)
        witnesses.append({'connection_id': row['connection_id'], 'original': baseline, 'candidate': objective})
    inputs = {str(root / name): sha(root / name) for root in (parent, search)
              for name in ('protocol.json', 'receipt.json')}
    inputs[str(parent / 'prediction.json')] = sha(parent / 'prediction.json')
    inputs[str(search / 'queries.jsonl')] = sha(search / 'queries.jsonl')
    report = {'inputs_sha256': inputs, 'connections_replayed': len(witnesses),
              'strict_lexicographic_improvements': sum(r['candidate'] < r['original'] for r in witnesses),
              'witnesses': witnesses,
              'scope': 'independent path/node reconstruction and overflow-difference arithmetic; per-path objective no worse than original feasible witness; single-net non-worsening only, not batch tree/native STA/QoR acceptance'}
    out = base / 'conv_layer_lex_objective_replay_2026-10-06'
    out.mkdir()
    shutil.copyfile(__file__, out / 'source.py')
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (out / 'receipt.json').write_text(json.dumps({'report_sha256': sha(out / 'report.json'),
                                               'source_sha256': sha(out / 'source.py'),
                                               'inputs_sha256': inputs}, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('inputs_sha256', 'witnesses')}), flush=True)


if __name__ == '__main__':
    run()
