"""Compare completed greedy shared-tree candidates with per-path development baseline."""
import collections
import json
import shutil
from pathlib import Path

from pre_route_endpoints import sha


def run():
    base = Path('experiments')
    shared = base / 'conv_layer_shared_tree_avoidance_2026-10-06'
    independent = base / 'conv_layer_budgeted_span_avoidance_2026-10-06'
    impact = base / 'conv_layer_shared_tree_whole_net_candidate_impact_2026-10-06/report.json'
    baseline = base / 'conv_layer_span_whole_net_candidate_impact_2026-10-06/report.json'
    matched = base / 'conv_layer_independent_two_net_candidate_impact_2026-10-06/report.json'
    chain = base / 'conv_layer_shared_tree_completion_chain_2026-10-06'
    sources = {Path(__file__).name: sha(__file__), 'pre_route_endpoints.py': sha(Path('tools/pre_route_endpoints.py'))}
    bindings = {str(p): sha(p) for p in (impact, baseline, matched, chain / 'receipt.json', chain / 'protocol.json')}
    cr = json.loads((chain / 'receipt.json').read_text())
    assert cr['protocol_sha256'] == sha(chain / 'protocol.json')
    assert len(cr['stages']) == 2 and all(s['exit_code'] == 0 for s in cr['stages'])
    cp = json.loads((chain / 'protocol.json').read_text())
    assert all(sha(chain / 'source' / n) == h for n, h in cp['source_sha256'].items())
    data = []
    for root, report_path in ((shared, impact), (independent, baseline)):
        receipt = json.loads((root / 'receipt.json').read_text())
        protocol = json.loads((root / 'protocol.json').read_text())
        assert receipt['protocol_sha256'] == sha(root / 'protocol.json')
        assert receipt['journal_sha256'] == sha(root / 'queries.jsonl')
        assert all(sha(p) == h for p, h in protocol['inputs_sha256'].items())
        assert all(sha(root / 'source' / n) == h for n, h in protocol['source_sha256'].items())
        report = json.loads(report_path.read_text())
        assert all(sha(p) == h for p, h in report['inputs_sha256'].items())
        assert report['incremental_equals_full_rebuild'] and not report['repair_committed']
        rows = [json.loads(s) for s in (root / 'queries.jsonl').read_text().splitlines()]
        assert len(rows) == receipt['queries']
        bindings.update({str(root / n): sha(root / n) for n in ('receipt.json', 'protocol.json', 'queries.jsonl')})
        data.append((protocol, report, rows))
    sp, si, sq = data[0]
    bp, bi, bq = data[1]
    mi = json.loads(matched.read_text())
    assert all(sha(p) == h for p, h in mi['inputs_sha256'].items())
    assert mi['inputs_sha256'] == bi['inputs_sha256']
    assert mi['incremental_equals_full_rebuild'] and not mi['repair_committed']
    assert set(mi['eligible_whole_net_ids']) == set(si['eligible_whole_net_ids']) == {5376, 7312}
    assert mi['overflow_before'] == si['overflow_before']
    assert sp['graph'] == bp['graph'] and sp['banned_channel_nodes'] == bp['banned_channel_nodes']
    bmap = {r['connection_id']: r for r in bq}
    increments = collections.Counter()
    assert len(sq) == 17 and set(si['eligible_whole_net_ids']) == {5376, 7312}
    for row in sq:
        assert row['result']['status'] == 'FOUND'
        old = bmap[row['connection_id']]
        assert all(row[k] == old[k] for k in ('net_id', 'source', 'sink', 'original_opin', 'original_ipin'))
        increments[row['net_id']] += row['result']['cost']
    comparison = []
    bspan = {r['net_id']: r for r in bi['net_span_changes']}
    for row in si['net_span_changes']:
        old = bspan[row['net_id']]
        assert row['old'] == old['old'] and increments[row['net_id']] == row['new']
        comparison.append({'net_id': row['net_id'], 'original_union_span': row['old'],
                           'independent_candidate_union_span': old['new'],
                           'greedy_shared_union_span': row['new']})
    assert mi['net_span_changes'] == [bspan[n] for n in sorted(mi['eligible_whole_net_ids'])]
    result = {'inputs_sha256': bindings, 'net_span_comparison': comparison,
              'shared_two_net_overflow_before': si['overflow_before'],
              'shared_two_net_overflow_after': si['overflow_after'],
              'shared_two_net_worsened_resources': si['worsened_resources'],
              'independent_two_net_overflow_after': mi['overflow_after'],
              'independent_two_net_worsened_resources': mi['worsened_resources'],
              'strict_span_improvement_nets': [r['net_id'] for r in si['net_span_changes'] if r['new'] < r['old']],
              'repair_committed': False,
              'scope': 'same 17 connection pins/budgets/graph/banned channels; full occupancy rebuilt for matched two-net batches; development greedy order, not unseen/native STA/QoR or end-to-end benefit'}
    assert all(sha(p) == h for p, h in bindings.items())
    out = base / 'conv_layer_shared_tree_objective_comparison_2026-10-06'
    out.mkdir()
    shutil.copyfile(__file__, out / 'source.py')
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    (out / 'receipt.json').write_text(json.dumps({'report_sha256': sha(out / 'report.json'),
                                               'source_sha256': sources, 'inputs_sha256': bindings}, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'inputs_sha256'}), flush=True)


if __name__ == '__main__':
    run()
