"""Import a complete external native source route with certified current floors.

Does not launch routing. Original XML arc/RC checks are reused; independent
native printed-tree audit must still follow this producer.
"""
import argparse
import json
import time
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent/'native_resume_prototype'))
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
from external_native_anchored_budget_v1 import assign, POLICY
from pre_route_endpoints import sha
from source_binding_v2 import closure

def prepare(endpoint, route, floor_proof, output):
    begin = time.perf_counter()
    endpoint, route, floor_proof, output = map(lambda p: Path(p).resolve(),
                                             (endpoint, route, floor_proof, output))
    meta = json.loads(endpoint.read_text())
    proof = json.loads(floor_proof.read_text())
    if proof['status'] != 'ALL_FRAME_RAW_FLOORS_ORIGIN_PROOFS_NEW_MINIMA_AND_CURRENT_XML_PATHS_VERIFIED':
        raise ValueError('certified frame floors required')
    if proof.get('objective') != 'XML_ZERO_RC_SWITCH_TDEL_POSITIVE_CAPACITY_SCALE1E18_V1':
        raise ValueError('unsupported floor objective')
    if proof['graph_sha256'] != meta['graph_sha256'] or proof['unreachable'] != 0:
        raise ValueError('graph mismatch or unreachable floor')
    floor_path = floor_proof.parent/'floors.jsonl'
    bindings = closure([Path(__file__)])
    for path, digest in proof['bindings'].items():
        if path in bindings and bindings[path] != digest:
            raise ValueError('conflicting binding')
        bindings[path] = digest
    if bindings.get(str(floor_path)) != sha(floor_path):
        raise ValueError('floor payload not bound')
    for path in (endpoint, route, floor_proof):
        bindings[str(path)] = sha(path)
    if not all(sha(p) == h for p,h in bindings.items()):
        raise ValueError('floor or implementation dependency changed')
    floors = {}
    for line in floor_path.read_text().splitlines():
        row = json.loads(line)
        if row['connection_id'] in floors:
            raise ValueError('duplicate floor CID')
        floors[row['connection_id']] = row
    graph, digest, nodes, fields, rc, queries = load_endpoints(endpoint)
    if digest != proof['graph_sha256'] or rc.scale != 10**18:
        raise ValueError('graph objective/scale mismatch')
    if len(queries) != proof['connections'] or set(floors) != {q['connection_id'] for q in queries}:
        raise ValueError('floor CID universe mismatch')
    paths, native_rows, ledger = load_complete(route, meta, nodes, fields, rc)
    if any(v > fields['capacities'][n] for n,v in ledger.occupancy.items()):
        raise ValueError('source route capacity overflow')
    by_id = {r['connection_id']:r for r in native_rows}
    records = []
    independent = Counter()
    for q in queries:
        cid = q['connection_id']; f = floors[cid]; r = by_id[cid]
        if any(f[k] != q[k] for k in ('connection_id','net_id','source','sink')):
            raise ValueError('floor endpoint mismatch')
        record = dict(q, floor_integer=f['minimum_integer'],
                      answer=dict(status='FOUND',physical_edge_ids=r['physical_edge_ids'],
                                  delay=r['delay_integer']))
        records.append(record)
        independent.update(n for n, switch in paths[cid])
    budgets = assign(records, records, digest, digest, rc.scale)
    for record, budget in zip(sorted(records,key=lambda r:r['connection_id']),budgets):
        record.update({k:budget[k] for k in ('budget_integer','proxy_budget_integer')})
    frame = dict(records=sorted(records,key=lambda r:r['connection_id']),scale=rc.scale,
                 graph_sha256=digest,required_connections=len(queries),
                 completed_connections=len(records),ledger=dict(ledger.occupancy),
                 independent_connection_ledger=dict(independent),history={},
                 epochs={str(q['net_id']):0 for q in queries},overflow_units=0,
                 budget_policy=POLICY,eligible_for_legal_route_commit=False)
    if not all(sha(p) == h for p,h in bindings.items()):
        raise ValueError('input changed during import')
    output.mkdir(exist_ok=False)
    initial = output/'initial.json'; initial.write_text(json.dumps(frame)+'\n')
    bindings[str(initial)] = sha(initial)
    receipt = dict(status='COMPLETE_SOURCE_IMPORTED_INDEPENDENT_NATIVE_AUDIT_PENDING',
                   bindings=bindings,connections=len(records),nets=len(ledger.nodes),
                   source_route=str(route),source_endpoint=str(endpoint),floor_proof=str(floor_proof),
                   total_producer_component_seconds=time.perf_counter()-begin,
                   independent_audit_pending=True,
                   scope='Original graph arcs, exact additive RC, full endpoint coverage and unique-NET occupancy checked. No native printed-tree independent audit or STA/quality/full-time claim.')
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt['status']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('endpoint','route','floor_proof','output'):
        parser.add_argument(name)
    args = parser.parse_args()
    print(prepare(args.endpoint,args.route,args.floor_proof,args.output))
