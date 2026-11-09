"""Full-design candidate occupancy replacement, rollback and epoch evidence.

An occupancy transaction is not native routing acceptance or a timing budget gate.
"""
import collections
import json
import shutil
import time
from array import array
from pathlib import Path
from types import SimpleNamespace

from incremental_channel_pressure import ChannelPressure
from connection_golden import Result
from pre_route_endpoints import sha
from prepared_csr import read
from rr_local_batch_occupancy import LocalBatchOccupancy
from streaming_prediction_audit import Edges, Nodes


def run():
    base = Path('experiments')
    design='adder_tree_2L_032bits'
    old_root=base/'adder_tree_family_predictions_2026-10-06'/design/'sparse_reset'
    moved=base/'adder_tree_2L032_moved_incremental_search_2026-10-06'
    swap=base/'adder_tree_2L032_placement_swap_2026-10-06'
    paths=[]
    def load(path):
        paths.append(path)
        return json.loads(path.read_text())
    old_receipt=load(old_root/'receipt.json')
    old_protocol=load(old_root/'protocol.json')
    assert old_receipt['prediction_sha256']==sha(old_root/'prediction.json')
    assert old_receipt['protocol_sha256']==sha(old_root/'protocol.json')
    mr=load(moved/'receipt.json')
    assert mr['prediction_sha256']==sha(moved/'prediction.json')
    assert mr['physical_audit_sha256']==sha(moved/'physical_audit.json')
    assert mr['paths_equal_full_moved_search']
    assert all(sha(p)==h for p,h in mr['inputs_sha256'].items())
    physical=load(moved/'physical_audit.json')
    assert physical['all_physical_and_union_checks_passed']
    ar=load(Path(str(old_root)+'_physical_audit')/'receipt.json')
    assert ar['prediction_receipt_sha256']==sha(old_root/'receipt.json')
    assert ar['result']['all_physical_and_union_checks_passed']
    predictions=[load(old_root/'prediction.json'),load(moved/'prediction.json')]
    closure=load(swap/'affected_source_closure.json')
    sr=load(swap/'receipt.json')
    assert sr['closure_sha256']==sha(swap/'affected_source_closure.json')
    assert sr['endpoint_sha256']==sha(swap/'endpoints.json')
    paths.append(swap/'endpoints.json')
    protocols=[old_protocol]
    m,f=read(base/'adder_tree_family_length_switch_csr_2026-10-06'/design/'csr',old_protocol['inputs']['graph']['sha256'])
    assert sha(base/'adder_tree_family_length_switch_csr_2026-10-06'/design/'csr/manifest.json')==old_protocol['csr_manifest_sha256']
    assert all(raw == rank for rank, raw in enumerate(f['node_ids']))
    slots = array('Q', [0]) * m['edges']
    for slot, eid in enumerate(f['edge_ids']):
        slots[eid] = slot
    edges = {}
    all_nodes = set()
    node_sets = []
    for pred in predictions:
        sets = {}
        for row in pred['connections']:
            current = row['source']
            touched = {current}
            for eid in row['physical_edge_ids']:
                slot = slots[eid]
                assert f['row_offsets'][current] <= slot < f['row_offsets'][current + 1]
                dest = f['dest_ranks'][slot]
                assert dest not in touched
                edges[eid] = SimpleNamespace(source=current, sink=dest, switch_id=f['switch_ids'][slot])
                touched.add(dest)
                current = dest
            assert current == row['sink']
            sets[row['connection_id']] = touched
            all_nodes.update(touched)
        node_sets.append(sets)
    rows = predictions[0]['connections']
    replacement = {r['connection_id']: r for r in predictions[1]['connections']}
    changed=closure['recompute_connection_ids']
    assert len(rows)==516 and len(changed)==118
    assert all(r==replacement[r['connection_id']] for r in rows if r['connection_id'] not in changed)
    nodes = Nodes(f['types'], f['capacities'])
    graph = SimpleNamespace(nodes={n: nodes[n] for n in all_nodes}, edges=Edges(edges, m['edges']))
    ledger = LocalBatchOccupancy(graph)

    def request(row, epoch):
        return {k: row[k] for k in ('connection_id', 'net_id', 'source', 'sink')} | {'epoch': epoch, 'edge_ids': row['physical_edge_ids']}

    def rebuilt(active, sets):
        nets = collections.defaultdict(set)
        for row in active:
            nets[row['net_id']].update(sets[row['connection_id']])
        return collections.Counter(n for touched in nets.values() for n in touched)

    def check(expected):
        actual = {n: v for n, v in ledger.occupancy.items() if v}
        assert actual == dict(expected)
        assert ledger.occupancy == ledger.rebuild()

    start = time.monotonic()
    assert ledger.update_batch([request(row, 1) for row in rows]) == Result.COMMITTED
    seed_s = time.monotonic() - start
    initial = rebuilt(rows, node_sets[0])
    assert dict(initial) == {int(n): v for n, v in predictions[0]['node_occupancy'].items()}
    check(initial)
    cache=ChannelPressure(f['types'],f['capacities'])
    cache.refresh(initial,all_nodes)
    original_payload=cache.payload(protocols[0]['inputs']['graph']['sha256'])
    dirty=set().union(*(node_sets[0][cid]|node_sets[1][cid] for cid in changed))
    states_before = ledger.states
    requests = [request(replacement[cid], 2) for cid in changed]
    start = time.monotonic()
    assert ledger.update_batch(requests) == Result.COMMITTED
    update_s = time.monotonic() - start
    pressure_start=time.monotonic()
    cache.refresh(ledger._occupancy,dirty)
    pressure_refresh_s=time.monotonic()-pressure_start
    pressure_start=time.monotonic()
    candidate_payload=cache.payload(protocols[0]['inputs']['graph']['sha256'])
    pressure_serialize_s=time.monotonic()-pressure_start
    full_cache=ChannelPressure(f['types'],f['capacities'])
    full_cache.refresh({int(n):v for n,v in predictions[1]['node_occupancy'].items()},all_nodes)
    assert candidate_payload==full_cache.payload(protocols[0]['inputs']['graph']['sha256'])
    before_cache=dict(cache.rows)
    try:cache.refresh(ledger._occupancy,[next(iter(dirty)),-1])
    except ValueError:pass
    else:raise AssertionError('invalid dirty node accepted')
    assert cache.rows==before_cache

    final = rebuilt(predictions[1]['connections'], node_sets[1])
    assert dict(final) == {int(n): v for n, v in predictions[1]['node_occupancy'].items()}
    check(final)
    states_after = ledger.states
    assert all(states_after[cid] == state for cid, state in states_before.items() if cid not in changed)
    assert ledger.update_batch(requests) == Result.STALE
    assert ledger.states == states_after
    check(final)
    mixed = [request(replacement[changed[0]], 3), request(replacement[changed[1]], 3)]
    mixed[1]['edge_ids'] = [-1]
    assert ledger.update_batch(mixed) == Result.INVALID
    assert ledger.states == states_after
    check(final)
    old_by_id = {r['connection_id']: r for r in rows}
    start = time.monotonic()
    assert ledger.update_batch([request(old_by_id[cid], 3) for cid in changed]) == Result.COMMITTED
    restore_s = time.monotonic() - start
    cache.refresh(ledger._occupancy,dirty)
    assert cache.payload(protocols[0]['inputs']['graph']['sha256'])==original_payload

    check(initial)
    net_counts = collections.Counter(r['net_id'] for r in rows)
    shared = next(r for r in rows if net_counts[r['net_id']] > 1)
    source_occupancy = ledger.occupancy[shared['source']]
    assert ledger.update_batch([{'connection_id': shared['connection_id'], 'epoch': 4, 'remove': True}]) == Result.COMMITTED
    check(rebuilt([r for r in rows if r['connection_id'] != shared['connection_id']], node_sets[0]))
    assert ledger.occupancy[shared['source']] == source_occupancy
    assert ledger.update_batch([request(shared, 5)]) == Result.COMMITTED
    check(initial)
    bindings = {str(p): sha(p) for p in paths}
    out = base / 'adder_tree_2L032_moved_incremental_pressure_2026-10-06'
    out.mkdir()
    (out / 'source').mkdir()
    names = [Path(__file__).name, 'rr_local_batch_occupancy.py', 'rr_occupancy.py',
             'incremental_channel_pressure.py', 'connection_golden.py', 'prepared_csr.py', 'streaming_prediction_audit.py', 'pre_route_endpoints.py']
    for n in names:
        shutil.copyfile(Path('tools') / n, out / 'source' / n)
    receipt = {'inputs_sha256': bindings, 'source_sha256': {n: sha(out / 'source' / n) for n in names},
               'connections':516,'replaced':118,'unchanged_states_exact':398,'dirty_nodes':len(dirty),'incremental_pressure_payload_byte_equals_full':True,'invalid_pressure_refresh_no_mutation':True,'pressure_refresh_s':pressure_refresh_s,'pressure_serialize_s':pressure_serialize_s,
               'incremental_equals_independent_full_rebuild': True,
               'stale_replay_no_mutation': True, 'mixed_invalid_batch_atomic': True,
               'restore_original_occupancy_exact': True, 'shared_trunk_remove_restore_verified': True,
               'seed_ledger_s': seed_s, 'candidate_ledger_update_s': update_s, 'restore_ledger_s': restore_s,
               'repair_committed': False,
               'scope': 'real preselected placement swap full-design occupancy transaction on originalXML-audited moved paths; ledger timings exclude search/conversion/indexing/export/rebuild and native routing; no electrical budget, accepted repair, unseen-family or end-to-end benefit claim'}
    assert all(sha(p) == h for p, h in bindings.items())
    (out/'candidate.pressure').write_text(candidate_payload)
    (out/'original.pressure').write_text(original_payload)
    receipt['pressure_sha256']={n:sha(out/n) for n in ('candidate.pressure','original.pressure')}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('inputs_sha256', 'source_sha256')}), flush=True)


if __name__ == '__main__':
    run()
