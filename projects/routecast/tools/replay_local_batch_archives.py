"""Actual archived RR path transactions; excludes search and native routing."""
import json
import argparse
import shutil
import time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from rr_local_batch_occupancy import LocalBatchOccupancy
from affected_connections import affected
from connection_golden import Result

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path,
                    default=Path('experiments/local_batch_archive_replay_2026-10-05'))
out = parser.parse_args().output
if out.exists():
    raise ValueError('fresh output required')
prior = Path('experiments/matched_hpwl_trial_2026-10-04')
base = Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json')
graph = Path(json.loads(base.read_text())['inputs']['graph']['path'])
inputs = {'graph': graph}
for number in range(1, 8):
    for kind in ('endpoints', 'prediction'):
        inputs[f'{number}_{kind}'] = prior/f'candidate_{number}_{kind}.json'
out.mkdir()
(out/'source').mkdir()
for name in ('replay_local_batch_archives.py', 'rr_local_batch_occupancy.py',
             'rr_occupancy.py', 'connection_golden.py', 'affected_connections.py',
             'rr_graph.py', 'pre_route_endpoints.py'):
    shutil.copy2(Path('tools')/name, out/'source'/name)
protocol = {'inputs': {name: {'path': str(path.resolve()), 'sha256': sha(path)}
                       for name, path in inputs.items()},
            'source_sha256': {p.name: sha(p) for p in (out/'source').iterdir()},
            'scope': 'Development archived-path ledger replay; no new search, conversion, '
                     'native QoR or end-to-end speed evidence.'}
(out/'protocol.json').write_text(json.dumps(protocol, indent=2)+'\n')
start = time.monotonic()
g = read_rr_graph(graph)
graph_s = time.monotonic()-start
ledger = LocalBatchOccupancy(g)
epochs = {}
before = None
reports = []
for number in range(1, 8):
    start = time.monotonic()
    after = json.loads(inputs[f'{number}_endpoints'].read_text())
    prediction = json.loads(inputs[f'{number}_prediction'].read_text())
    load_s = time.monotonic()-start
    assert prediction['physical_graph_sha256'] == sha(graph)
    start = time.monotonic()
    closure = affected(before, after) if before else None
    ids = set(closure['recompute_connection_ids']) if closure else {
        r['connection_id'] for r in after['connections']}
    rows = {r['connection_id']: r for r in prediction['connections']}
    endpoint_rows = {r['connection_id']: r for r in after['connections']}
    assert len(rows) == len(prediction['connections'])
    assert len(endpoint_rows) == len(after['connections'])
    assert set(rows) == set(endpoint_rows)
    for cid, row in rows.items():
        assert all(row[k] == endpoint_rows[cid][k] for k in
                   ('connection_id', 'net_id', 'source', 'sink'))
    updates = []
    for cid in sorted(ids):
        row = rows[cid]
        epochs[cid] = epochs.get(cid, 0)+1
        updates.append({k: row[k] for k in ('connection_id', 'net_id', 'source', 'sink')} |
                       {'epoch': epochs[cid], 'edge_ids': row['physical_edge_ids']})
    for cid in (closure['remove_connection_ids'] if closure else []):
        epochs[cid] = epochs.get(cid, 0)+1
        updates.append({'connection_id': cid, 'epoch': epochs[cid], 'remove': True})
    prepare_s = time.monotonic()-start
    start = time.monotonic()
    if updates:
        assert ledger.update_batch(updates) == Result.COMMITTED
    commit_s = time.monotonic()-start
    start = time.monotonic()
    for cid, (_, conn) in ledger.states.items():
        if conn is not None:
            row = rows[cid]
            assert (conn.net_id, conn.source, conn.sink, conn.edge_ids) == (
                row['net_id'], row['source'], row['sink'], tuple(row['physical_edge_ids']))
    assert {cid for cid, (_, conn) in ledger.states.items() if conn is not None} == set(rows)
    occupancy = {str(n): v for n, v in ledger.occupancy.items() if v}
    assert occupancy == prediction['node_occupancy']
    assert ledger.occupancy == ledger.rebuild()
    reports.append({'candidate': number, 'changed_batch': len(updates),
                    'load_s': load_s, 'closure_and_prepare_s': prepare_s,
                    'commit_s': commit_s, 'independent_validation_s': time.monotonic()-start,
                    'exact_full_paths_and_occupancy': True})
    before = after
    print(json.dumps(reports[-1]), flush=True)
assert all(sha(v['path']) == v['sha256'] for v in protocol['inputs'].values())
(out/'receipt.json').write_text(json.dumps({'protocol_sha256': sha(out/'protocol.json'),
    'graph_load_s': graph_s, 'reports': reports, 'inputs_unchanged': True,
    'scope': protocol['scope']}, indent=2)+'\n')
