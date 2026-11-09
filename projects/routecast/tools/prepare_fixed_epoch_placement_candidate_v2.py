"""Prepare an isolated placement candidate using authenticated frozen routing epochs."""
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(R / 'tools'), str(R / 'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from frozen_timing_epoch_remap_v1 import remap
from affected_connections import affected
from audit_structural_node_base_v1 import audit as audit_base
from class_cached_rc_endpoint_context_v1 import load_endpoints
from load_design_routing_inputs_v2 import load
from sparse_structural_objective_search_v1 import Search


def prepare(cohort_directory, candidate_id, output, previous_model):
    start = time.perf_counter()
    cohort, output = Path(cohort_directory).resolve(), Path(output).resolve()
    output.mkdir()
    cp = cohort / 'verification.json'
    certified = json.loads(cp.read_text())
    assert certified['all_eight_legal_moves_and_complete_endpoint_identity_pass']
    assert not certified['native_route_labels_generated']
    assert all(sha(p) == h for p, h in certified['bindings'].items())
    row = next(r for r in certified['rows'] if r['candidate_id'] == candidate_id)
    protocol = json.loads((cohort / 'protocol.json').read_text())
    before = Path(protocol['baseline_endpoint'])
    endpoint = Path(row['endpoint'])
    original = Path(previous_model).resolve()
    old_criticality = R / 'experiments/xtea_retained_native_inputs_v1_2026-10-13/criticality'
    old_manifest = R / 'experiments/xtea_retained_input_preflight_v1_2026-10-13/xtea.queries'
    old_base = R / 'experiments/xtea_retained_node_base_v1_2026-10-13/verification.json'
    bindings = {**closure([Path(__file__)]), **certified['bindings'], str(cp): sha(cp)}
    a, b = [json.loads(p.read_text()) for p in [before, endpoint]]
    assert a['graph_sha256'] == b['graph_sha256'] and a['inputs']['net']['sha256'] == b['inputs']['net']['sha256']
    # Native objects preserve the exact NET/local-pin/logical identity; only position changes.
    identities = []
    for ep in [a, b]:
        path = Path(ep['inputs']['native_identity']['path'])
        identities.append([json.loads(line) for line in path.read_text().splitlines()])
    def logical_identity(rows):
        return [dict(r, pins=[{k: v for k, v in p.items() if k not in ['x', 'y', 'layer']} for p in r['pins']]) for r in rows]
    assert logical_identity(identities[0]) == logical_identity(identities[1])
    values, epoch_bindings, epoch = remap(before, endpoint, old_criticality, old_manifest, row['manifest'])
    timing = output / 'timing'
    timing.mkdir()
    vector = timing / 'remapped_criticalities.json'
    vector.write_text(json.dumps([dict(values[k]) for k in sorted(values)], separators=(',', ':')) + '\n')
    epoch_bindings.update(bindings)
    epoch_bindings[str(vector)] = sha(vector)
    timing_proof = dict(schema='ROUTECAST_FROZEN_TIMING_REMAP_V1', bindings=epoch_bindings, timing_epoch_sha256=epoch, before_endpoint=str(before), after_endpoint=str(endpoint), source_criticality_directory=str(old_criticality), before_manifest=str(old_manifest), after_manifest=row['manifest'], connections=len(values), all_native_pin_identities_preserved=True, all_values_equal_before_timing_epoch=True, all_endpoints_equal_after_placement=True, scope='Original native timing epoch, remapped by stable NET/local-pin identities and independently checked native logical pin objects. No post-move STA input.')
    (timing / 'verification.json').write_text(json.dumps(timing_proof, indent=2) + '\n')

    # Explicitly keep the initialized node-cost epoch on the byte-identical graph.
    base = output / 'base'
    base.mkdir()
    source = json.loads(old_base.read_text())
    assert all(sha(p) == h for p, h in source['bindings'].items())
    payload = base / 'node_base.u64'
    payload.write_bytes((old_base.parent / 'node_base.u64').read_bytes())
    base_bindings = {**source['bindings'], **bindings, str(old_base): sha(old_base), str(payload): sha(payload), str(endpoint): sha(endpoint)}
    source.update(bindings=base_bindings, scope='Frozen initialized node-base epoch transferred across a placement-only change on the identical graph; independently rebuilt from original XML and native cost-index float32 bits. Not a fresh native observation.')
    base_proof = base / 'verification.json'
    base_proof.write_text(json.dumps(source, indent=2) + '\n')
    audited_base = audit_base(b['inputs']['graph']['path'], base_proof, source['scale'])
    graph, digest, nodes, fields, rc, queries = load_endpoints(endpoint)
    bases, cs, extra = load(endpoint, base_proof, timing, len(nodes), rc.scale)
    assert bases == audited_base and len(cs) == len(queries)
    bindings.update(extra)
    for name in ['verification.json', 'initial_physical_verification.json', 'sketch_physical_verification.json']:
        p = original / name
        v = json.loads(p.read_text())
        assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
        assert all(sha(q) == h for q, h in v['bindings'].items())
        bindings.update(v['bindings'])
        bindings[str(p)] = sha(p)
    prior, last = [json.loads((original / name).read_text()) for name in ['sketch.json', 'round1.json']]
    for name in ['sketch.json', 'round1.json']:
        bindings[str(original / name)] = sha(original / name)
    delta = affected(a, b)
    dirty = set(delta['affected_net_ids'])
    old_records = {r['connection_id']: r for r in prior['records']}
    groups = defaultdict(list)
    for q in queries:
        groups[q['net_id']].append(q)
    binary = R / 'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so'
    bindings[str(binary)] = sha(binary)
    records = []

    def fresh_records(search, qs):
        src = qs[0]['source']
        assert all(q['source'] == src for q in qs)
        distances, parents, settled = search.search(src, {q['sink'] for q in qs})
        answer = []
        for q in sorted(qs, key=lambda q: q['connection_id']):
            assert q['sink'] in settled
            u, edges, seen = q['sink'], [], {q['sink']}
            while u != src:
                u, index = parents[u]
                assert u not in seen
                seen.add(u)
                edges.append(fields['edge_ids'][index])
            edges.reverse()
            floor = distances[q['sink']]
            assert rc.path(src, q['sink'], edges) == floor
            answer.append(dict(q, answer=dict(status='FOUND', physical_edge_ids=edges, delay=floor), floor_integer=floor, budget_integer=max(rc.scale // 10**9, (3 * floor + 1) // 2)))
        return answer

    search = Search(fields, rc, binary, bases)
    search.prepare({}, 0, structural=False)
    tick = time.perf_counter()
    for net, qs in sorted(groups.items()):
        if net in dirty:
            records.extend(fresh_records(search, qs))
        else:
            for q in qs:
                rec = old_records[q['connection_id']]
                assert all(rec[k] == v for k, v in q.items())
                records.append(rec)
    production_search_seconds = time.perf_counter() - tick
    search.close()
    # A fresh workspace recomputes every NET, solely as a full-rebuild audit.
    tick = time.perf_counter()
    reference = Search(fields, rc, binary, bases)
    reference.prepare({}, 0, structural=False)
    oracle = {r['connection_id']: r for net, qs in sorted(groups.items()) for r in fresh_records(reference, qs)}
    reference.close()
    for rec in records:
        if rec['net_id'] in dirty:
            assert rec == oracle[rec['connection_id']]
        else:
            assert rec == old_records[rec['connection_id']]
            assert rec['floor_integer'] == oracle[rec['connection_id']]['floor_integer']
    full_rebuild_audit_seconds = time.perf_counter() - tick
    slots = {eid: i for i, eid in enumerate(fields['edge_ids'])}
    owners, independent, floors = defaultdict(set), Counter(), {}
    for rec in records:
        used = {rec['source']} | {fields['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids']}
        owners[rec['net_id']].update(used)
        independent.update(used)
        key = rec['source'], rec['sink']
        assert key not in floors or floors[key] == rec['floor_integer']
        floors[key] = rec['floor_integer']
    ledger = Counter(n for owned in owners.values() for n in owned)
    overflow = sum(max(0, v - fields['capacities'][n]) for n, v in ledger.items())
    epochs = {int(n): e + int(int(n) in dirty) for n, e in last['epochs'].items()}
    frame = dict(prior, records=sorted(records, key=lambda r: r['connection_id']), ledger=dict(ledger), independent_connection_ledger=dict(independent), overflow_units=overflow, overflow_nodes=sum(v > fields['capacities'][n] for n, v in ledger.items()), epochs=epochs, scope='Isolated staged placement candidate; previous unaffected routes and history retained. No authoritative placement commit.')
    warm = output / 'warm'
    warm.mkdir()
    (warm / 'initial.json').write_text(json.dumps(frame) + '\n')
    (warm / 'floors.json').write_text(json.dumps([dict(source=s, sink=t, minimum_integer=v) for (s, t), v in sorted(floors.items())]) + '\n')
    (warm / 'history.json').write_text(json.dumps(last['prices']) + '\n')
    scope_file = warm / 'affected_scope.json'
    scope_file.write_text(json.dumps(dict(affected=delta, before_endpoint=str(before), after_endpoint=str(endpoint)), indent=2) + '\n')
    for p in warm.iterdir():
        bindings[str(p)] = sha(p)
    assert all(sha(p) == h for p, h in bindings.items())
    proof = dict(bindings=bindings, endpoint=str(endpoint), previous_model=str(original), affected_scope=str(scope_file), dirty_nets=sorted(dirty), required_connections=len(records), recomputed_connections=len(delta['recompute_connection_ids']), zero_price_source_search_calls=len(dirty), search_and_record_preparation_seconds=production_search_seconds, full_rebuild_audit_seconds=full_rebuild_audit_seconds, whole_preparation_seconds=time.perf_counter() - start, old_unaffected_records_exactly_preserved=True, dirty_records_equal_independent_full_initial=True, epochs_carried_and_dirty_bumped=True, history_exactly_previous_round1=True, scope='Production dirty-only source searches, compared with a separate fresh-workspace allNET zero-cost rebuild using the same search implementation. Original XML physical and event audits are mandatory downstream. Full-rebuild audit time included in whole preparation and reported separately; no native or net-gain claim.')
    (warm / 'verification.json').write_text(json.dumps(proof, indent=2) + '\n')
    print('CANDIDATE PREPARED', candidate_id, len(dirty), 'NETs', overflow, flush=True)


if __name__ == '__main__':
    prepare(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4])
