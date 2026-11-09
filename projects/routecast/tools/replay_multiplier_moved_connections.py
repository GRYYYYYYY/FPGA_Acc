"""Real fixed swap: closure-only search versus independent full moved search."""
import collections
import json
import shutil
import subprocess
import time
from pathlib import Path
from affected_connections import affected
from pre_route_endpoints import sha
from prepared_csr import read, U64
from streaming_prediction_audit import verify


def main():
    base = Path('experiments')
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('design',choices=[f'mult_{w}x{w}' for w in range(4,10)]);args=parser.parse_args();design=args.design
    swap = base / 'multiplier_placement_swap_2026-10-06' / design
    front = base / 'multiplier_family_endpoints_2026-10-06' / design
    baseline = base / 'multiplier_family_predictions_2026-10-06' / design / 'sparse_reset'
    prepared = base / 'multiplier_family_length_switch_csr_2026-10-06' / design
    out = base / 'multiplier_moved_incremental_search_2026-10-06' / design
    bindings = {}

    def load(path):
        bindings[str(path)] = sha(path)
        return json.loads(path.read_text())

    sr, sp = load(swap / 'receipt.json'), load(swap / 'protocol.json')
    assert sr['protocol_sha256'] == sha(swap / 'protocol.json')
    assert sr['endpoint_sha256'] == sha(swap / 'endpoints.json')
    assert sr['swapped_place_sha256'] == sha(swap / 'swapped.place')
    before, after = load(front / 'endpoints.json'), load(swap / 'endpoints.json')
    closure = affected(before, after)
    assert closure == load(swap / 'affected_source_closure.json')
    old, br = load(baseline / 'prediction.json'), load(baseline / 'receipt.json')
    assert br['prediction_sha256'] == sha(baseline / 'prediction.json') and br['failed'] == 0
    bp = load(baseline / 'protocol.json')
    binary = Path('build/routecast_csr_authenticated_sparse_reset')
    assert sha(binary) == bp['binary_sha256']
    bindings[str(binary)] = sha(binary)
    prep = load(prepared / 'receipt.json')
    assert prep['manifest_sha256'] == sha(prepared / 'csr/manifest.json') == bp['csr_manifest_sha256']
    assert after['graph_sha256'] == before['graph_sha256'] == old['physical_graph_sha256']
    for entry in sp['inputs'].values():
        assert sha(entry['path']) == entry['sha256']
        bindings[entry['path']] = entry['sha256']
    m, f = read(prepared / 'csr', after['graph_sha256'])
    slots = [0] * m['edges']
    for slot, eid in enumerate(f['edge_ids']):
        slots[eid] = slot
    out.mkdir(parents=True)
    names = ('replay_multiplier_moved_connections.py', 'affected_connections.py',
             'prepared_csr.py', 'pre_route_endpoints.py', 'streaming_prediction_audit.py',
             'physical_prediction_audit.py')
    (out / 'source').mkdir()
    for name in names:
        shutil.copyfile(Path('tools') / name, out / 'source' / name)
        bindings[str(Path('tools') / name)] = sha(Path('tools') / name)

    def search(cohort, tag):
        start = time.monotonic()
        groups = collections.defaultdict(list)
        for row in cohort:
            groups[row['net_id']].append(row)
        rows = []
        with (out / (tag + '_stderr.log')).open('w') as error:
            worker = subprocess.Popen([str(binary.resolve()), str((prepared / 'csr').resolve()), '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=error, text=True)
            try:
                with (out / (tag + '_journal.jsonl')).open('w') as journal:
                    for net, group in sorted(groups.items()):
                        sources = {r['source'] for r in group}
                        assert len(sources) == 1
                        source = next(iter(sources))
                        sinks = sorted({r['sink'] for r in group})
                        worker.stdin.write(' '.join(map(str, [source, *sinks])) + '\n')
                        worker.stdin.flush()
                        result = json.loads(worker.stdout.readline())
                        assert not result['budget_exhausted']
                        journal.write(json.dumps({'net_id': net, 'result': result}) + '\n')
                        for row in group:
                            path = result['paths'][str(row['sink'])]
                            rows.append({**row, 'physical_edge_ids': path, 'method': 'sparse_reset'})
                worker.stdin.close()
                assert worker.wait(timeout=30) == 0
            finally:
                if worker.poll() is None:
                    worker.terminate()
                    worker.wait()
        return rows, time.monotonic() - start

    selected = set(closure['recompute_connection_ids'])
    partial, partial_s = search([r for r in after['connections'] if r['connection_id'] in selected], 'incremental')
    retained = [r for r in old['connections'] if r['connection_id'] not in selected]
    incremental = sorted(retained + partial, key=lambda r: r['connection_id'])
    full, full_s = search(after['connections'], 'full')
    full.sort(key=lambda r: r['connection_id'])
    assert incremental == full
    occupancy = collections.Counter()
    unions = collections.defaultdict(set)
    for row in full:
        node = row['source']
        seen = {node}
        for eid in row['physical_edge_ids']:
            slot = slots[eid]
            assert f['row_offsets'][node] <= slot < f['row_offsets'][node + 1] and f['costs'][slot] != U64
            node = f['dest_ranks'][slot]
            assert node not in seen and f['capacities'][node] > 0
            seen.add(node)
        assert node == row['sink']
        unions[row['net_id']].update(seen)
    for nodes in unions.values():
        occupancy.update(nodes)
    prediction = {'physical_graph_sha256': after['graph_sha256'], 'connections': full,
                  'node_occupancy': {str(n): v for n, v in occupancy.items()},
                  'requested': len(full), 'completed': len(full),
                  'methods': {'sparse_reset': len(full)}}
    (out / 'prediction.json').write_text(json.dumps(prediction) + '\n')
    physical = verify(sp['inputs']['graph']['path'], after, prediction)
    (out / 'physical_audit.json').write_text(json.dumps(physical, indent=2) + '\n')
    assert all(sha(path) == digest for path, digest in bindings.items())
    report = {'inputs_sha256': bindings, 'connections': len(full), 'recomputed': len(partial),
              'retained_exact': len(retained), 'paths_equal_full_moved_search': True,
              'closure': closure, 'partial_search_process_s': partial_s, 'full_search_process_s': full_s,
              'prediction_sha256': sha(out / 'prediction.json'), 'physical_audit_sha256': sha(out / 'physical_audit.json'),
              'scope': 'Real preselected compatible CLB swap; frozen cost independent per-net search. Timings include consumer startup/search, exclude projection/CSR/index/occupancy/audit/native. No accepted repair, joint native legality or end-to-end gain.'}
    (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('inputs_sha256', 'closure')}), flush=True)


if __name__ == '__main__':
    main()
