"""Policy-specific net span lower bounds from completed optimistic Pareto search.

Independent path objectives lower-bound a shared union by their maximum, never
their sum. This is a development diagnostic, not a native routing certificate.
"""
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
    search = base / 'conv_layer_budgeted_span_avoidance_2026-10-06'
    replay = base / 'conv_layer_candidate_span_objective_replay_2026-10-06'
    paths = [parent / 'protocol.json', parent / 'receipt.json',
             parent / 'prediction.json', search / 'protocol.json',
             search / 'receipt.json', search / 'queries.jsonl',
             replay / 'receipt.json']
    bindings = {str(p): sha(p) for p in paths}
    pp = json.loads(paths[0].read_text())
    pr = json.loads(paths[1].read_text())
    sp = json.loads(paths[3].read_text())
    sr = json.loads(paths[4].read_text())
    assert pr['protocol_sha256'] == bindings[str(paths[0])]
    assert pr['prediction_sha256'] == bindings[str(paths[2])]
    assert sr['protocol_sha256'] == bindings[str(paths[3])]
    assert sr['journal_sha256'] == bindings[str(paths[5])]
    assert sr['queries'] == 75 and sr['statuses'].get('LABEL_LIMIT', 0) == 0
    assert all(sha(p) == h for p, h in sp['inputs_sha256'].items())
    assert all(sha(search / 'source' / n) == h
               for n, h in sp['source_sha256'].items())
    m, f = read(base / 'conv_layer_length_switch_csr_2026-10-06/csr',
                pp['inputs']['graph']['sha256'])
    assert sha(base / 'conv_layer_length_switch_csr_2026-10-06/csr/manifest.json') == pp['csr_manifest_sha256']
    slots = array('Q', [0]) * m['edges']
    for slot, eid in enumerate(f['edge_ids']):
        slots[eid] = slot

    def nodes(row, edges):
        current = row['source']
        used = {current}
        for eid in edges:
            slot = slots[eid]
            assert f['row_offsets'][current] <= slot < f['row_offsets'][current + 1]
            current = f['dest_ranks'][slot]
            assert current not in used
            used.add(current)
        assert current == row['sink']
        return used

    def span(used):
        return sum(max(f['xhigh'][n] - f['xlow'][n],
                       f['yhigh'][n] - f['ylow'][n]) + 1
                   for n in used if f['types'][n] in (4, 5))

    original = json.loads(paths[2].read_text())['connections']
    by_id = {r['connection_id']: r for r in original}
    queries = [json.loads(s) for s in paths[5].read_text().splitlines()]
    assert len(queries) == 75 and len({r['connection_id'] for r in queries}) == 75
    grouped = collections.defaultdict(list)
    for r in queries:
        old = by_id[r['connection_id']]
        assert all(r[k] == old[k] for k in ('net_id', 'source', 'sink'))
        if r['result']['status'] == 'FOUND':
            assert span(nodes(r, r['result']['physical_edge_ids'])) == r['result']['cost']
        else:
            assert r['result']['status'] == 'UNREACHABLE'
        grouped[r['net_id']].append(r)
    records = []
    for net, rows in sorted(grouped.items()):
        full = [r for r in original if r['net_id'] == net]
        assert {r['connection_id'] for r in full} == {r['connection_id'] for r in rows}
        union = set()
        for r in full:
            union.update(nodes(r, r['physical_edge_ids']))
        old_span = span(union)
        feasible = all(r['result']['status'] == 'FOUND' for r in rows)
        lower = max(r['result']['cost'] for r in rows) if feasible else None
        records.append({'net_id': net, 'connections': len(rows),
                        'original_union_span': old_span,
                        'optimistic_union_span_lower_bound': lower,
                        'bound_exact_for_single_connection': len(rows) == 1 and feasible,
                        'strict_span_improvement_ruled_out_under_policy':
                            not feasible or lower >= old_span})
    assert len(records) == 49
    report = {'inputs_sha256': bindings, 'nets': records,
              'single_connection_nets': sum(r['connections'] == 1 for r in records),
              'single_connection_strict_improvement_ruled_out': sum(
                  r['connections'] == 1 and r['strict_span_improvement_ruled_out_under_policy']
                  for r in records),
              'multi_connection_nets_with_improvement_not_ruled_out': [
                  r['net_id'] for r in records if r['connections'] > 1 and
                  not r['strict_span_improvement_ruled_out_under_policy']],
              'scope': 'fixed original pins, original exact path budgets, all selected ten channels forbidden, other-net occupancy relaxed; max per-path minima lower-bounds union; no free-pin, alternate forbidden-set, tree feasibility or native STA claim',
              'repair_committed': False}
    assert all(sha(p) == h for p, h in bindings.items())
    out = base / 'conv_layer_avoidance_span_lower_bounds_2026-10-06'
    out.mkdir()
    shutil.copyfile(__file__, out / 'source.py')
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (out / 'receipt.json').write_text(json.dumps({
        'report_sha256': sha(out / 'report.json'),
        'source_sha256': sha(out / 'source.py'),
        'inputs_sha256': bindings}, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('inputs_sha256', 'nets')}), flush=True)


if __name__ == '__main__':
    run()
