"""Authenticated full-cohort development comparison; timing is descriptive only."""
import json
import shutil
from collections import Counter
from pathlib import Path

from pre_route_endpoints import sha


def prediction(root):
    protocol = json.loads((root / 'protocol.json').read_text())
    receipt = json.loads((root / 'receipt.json').read_text())
    assert receipt['protocol_sha256'] == sha(root / 'protocol.json')
    assert receipt['prediction_sha256'] == sha(root / 'prediction.json')
    assert receipt['journal_sha256'] == sha(root / 'net_results.jsonl')
    assert sha(root / 'consumer') == protocol['binary_sha256']
    assert all(sha(v['path']) == v['sha256'] for v in protocol['inputs'].values())
    assert all(sha(root / 'source' / Path(n).name) == h for n, h in protocol['source_sha256'].items())
    data = json.loads((root / 'prediction.json').read_text())
    results = [json.loads(s) for s in (root / 'net_results.jsonl').read_text().splitlines()]
    assert len(results) == receipt['nets'] == 12867
    assert len({r['net_id'] for r in results}) == 12867
    assert sum(r['result']['edge_visits'] for r in results) == receipt['edge_visits']
    assert sum(r['result']['settled_nodes'] for r in results) == receipt['settled_nodes']
    assert len(data['connections']) == receipt['connections'] == 21140
    assert sum(r['physical_edge_ids'] is None for r in data['connections']) == receipt['failed']
    return protocol, receipt, data, results


def evaluation(root, parent, pp, pr):
    protocol = json.loads((root / 'protocol.json').read_text())
    receipt = json.loads((root / 'receipt.json').read_text())
    assert receipt['protocol_sha256'] == sha(root / 'protocol.json')
    assert receipt['spatial_maps_sha256'] == sha(root / 'spatial_maps.json')
    assert receipt['exact_full_cohort_match'] and receipt['inputs_unchanged']
    assert all(sha(v['path']) == v['sha256'] for v in protocol['inputs'].values())
    assert all(sha(root / 'source' / n) == h for n, h in protocol['source_sha256'].items())
    assert protocol['inputs']['prediction']['sha256'] == pr['prediction_sha256']
    assert all(protocol['inputs'][k] == pp['inputs'][k] for k in ('graph', 'endpoints'))
    audit = Path(str(parent) + '_physical_audit')
    ar = json.loads((audit / 'receipt.json').read_text())
    ap = json.loads((audit / 'protocol.json').read_text())
    assert protocol['physical_audit_receipt_sha256'] == sha(audit / 'receipt.json')
    assert ar['protocol_sha256'] == sha(audit / 'protocol.json')
    assert ar['prediction_receipt_sha256'] == sha(parent / 'receipt.json')
    assert ar['result']['all_physical_and_union_checks_passed']
    assert ar['result']['requested'] == 21140 and ar['result']['completed'] == 21140 - pr['failed']
    assert all(sha(v['path']) == v['sha256'] for v in ap['inputs'].values())
    assert all(sha(audit / 'source' / n) == h for n, h in ap['source_sha256'].items())
    return protocol, receipt['reports']


def run():
    base = Path('experiments')
    roots = [base / 'conv_layer_length_switch_prediction_v2_2026-10-06',
             base / 'conv_layer_length_switch_sparse_reset_prediction_2026-10-06',
             base / 'conv_layer_length_switch_bbox3_prediction_2026-10-06']
    loaded = [prediction(root) for root in roots]
    p, r, d, journal = loaded[0]
    sp, sr, sd, sj = loaded[1]
    bp, br, bd, bj = loaded[2]
    assert sp['inputs'] == bp['inputs'] == p['inputs']
    assert sp['csr_manifest_sha256'] == bp['csr_manifest_sha256'] == p['csr_manifest_sha256']
    assert sp['reference_receipt_sha256'] == sha(roots[0] / 'receipt.json')
    assert sr['all_reference_net_paths_and_counters_exact'] and sr['full_prediction_semantically_exact']
    assert d == sd and journal == sj, 'independent full prediction and journal comparison failed'
    identity = lambda rows: Counter(tuple(row[k] for k in ('connection_id', 'net_id', 'source', 'sink')) for row in rows)
    assert identity(d['connections']) == identity(bd['connections'])
    eval_roots = [base / 'conv_layer_length_switch_evaluation_v2_2026-10-06',
                  base / 'conv_layer_bbox3_evaluation_2026-10-06']
    ep, er = evaluation(eval_roots[0], roots[0], p, r)
    be, ber = evaluation(eval_roots[1], roots[2], bp, br)
    assert ep['inputs']['native'] == be['inputs']['native']
    assert ep['native_audit_receipt_sha256'] == be['native_audit_receipt_sha256']
    native = base / 'conv_layer_native_route_labels_audit_v2_2026-10-06'
    nr = json.loads((native / 'receipt.json').read_text())
    np = json.loads((native / 'protocol.json').read_text())
    assert ep['native_audit_receipt_sha256'] == sha(native / 'receipt.json')
    assert nr['protocol_sha256'] == sha(native / 'protocol.json')
    assert nr['physical_checks_pass'] and nr['retained_endpoint_multiset_exact']
    assert nr['outputs']['physical_branches.json'] == ep['inputs']['native']['sha256']
    assert all(sha(v['path']) == v['sha256'] for v in np['inputs'].values())
    assert all(sha(native / 'source' / name) == h for name, h in np['source_sha256'].items())
    for name in ('prediction_metrics.py', 'stream_metric_domain.py', 'pre_route_endpoints.py'):
        assert ep['source_sha256'][name] == be['source_sha256'][name]
    differences = {}
    for domain in ('resource', 'spatial'):
        for key in ('k', 'universe_size', 'top_k_tie_rule', 'truth_k_boundary', 'nonzero_truth'):
            assert er[domain][key] == ber[domain][key]
        differences[domain] = {key: {'baseline': er[domain][key], 'bbox3': ber[domain][key],
                                    'bbox3_minus_baseline': ber[domain][key] - er[domain][key]}
                               for key in ('spearman', 'precision_at_k', 'recall_at_k', 'mae')}
    old = {row['connection_id']: row for row in d['connections']}
    changed = [row['connection_id'] for row in bd['connections']
               if row['physical_edge_ids'] != old[row['connection_id']]['physical_edge_ids']]
    bindings = {str(root / name): sha(root / name) for root in roots
                for name in ('protocol.json', 'receipt.json', 'prediction.json', 'net_results.jsonl')}
    bindings.update({str(root / name): sha(root / name) for root in eval_roots
                     for name in ('protocol.json', 'receipt.json', 'spatial_maps.json')})
    report = {'inputs_sha256': bindings, 'sparse_full_prediction_and_journal_exact': True,
              'bbox3_changed_connection_ids': changed, 'bbox3_failed_connections': br['failed'],
              'metric_differences': differences,
              'overflow': {'baseline': er['prediction_overflow_units'], 'bbox3': ber['prediction_overflow_units']},
              'descriptive_timings': {name: {'full_prediction_wall_s': record['full_prediction_wall_s'],
                                            'search_ledger_s': record['search_ledger_s'],
                                            'cold_conversion_wall_s': record['cold_conversion_wall_s'],
                                            'edge_visits': record['edge_visits'], 'settled_nodes': record['settled_nodes']}
                                      for name, record in zip(('baseline', 'sparse_reset', 'bbox3'), (r, sr, br))},
              'scope': 'authenticated development full-cohort comparison; concurrent and different run times are descriptive, not controlled end-to-end speedup; induced-subgraph failures not full-graph infeasibility; no unseen-family/native QoR/device or feedback benefit claim'}
    assert all(sha(path) == h for path, h in bindings.items())
    out = base / 'conv_layer_search_variant_comparison_2026-10-06'
    out.mkdir()
    shutil.copyfile(__file__, out / 'source.py')
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (out / 'receipt.json').write_text(json.dumps({'report_sha256': sha(out / 'report.json'),
                                               'source_sha256': sha(out / 'source.py'), 'inputs_sha256': bindings}, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('inputs_sha256', 'bbox3_changed_connection_ids')}), flush=True)


if __name__ == '__main__':
    run()
