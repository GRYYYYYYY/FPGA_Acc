"""Authenticated real graph census; no quotient route substitution."""
import json
import sys
from array import array
from collections import Counter
from pathlib import Path
from time import perf_counter

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from zero_rc_scc_bridge_v1 import partition

name = sys.argv[1]
assert name in ['xtea', '8051', 'mmc']
protocol_path = R/'experiments/resident_radix_count_complete_v4_2026-10-08/protocol.json'
protocol = json.loads(protocol_path.read_text())
assert all(sha(p) == h for p, h in protocol['bindings'].items())
endpoint = Path(next(x['endpoint'] for x in protocol['cases'] if x['name'] == name))
binary = R/'experiments/zero_rc_scc_build_v1_2026-10-08/scc.so'
contract_path = R/'experiments/zero_rc_scc_contract_v1_2026-10-08/verification.json'
contract = json.loads(contract_path.read_text())
assert contract['pass_all'] and all(sha(R/p) == h for p,h in contract['bindings'].items())
bindings = {**closure([Path(__file__)]), str(protocol_path):sha(protocol_path),
            str(endpoint):sha(endpoint), str(binary):sha(binary),
            str(contract_path):sha(contract_path)}
graph, digest, nodes, fields, rc, queries = load_endpoints(endpoint)
bindings[str(graph)] = digest
start = perf_counter()
labels, count = partition(fields, rc.increments, binary)
partition_seconds = perf_counter() - start
sizes = Counter(labels[u] for u,c in enumerate(fields['capacities']) if c)
zero_edges = internal_edges = 0
for u,c in enumerate(fields['capacities']):
    if not c:
        continue
    for e in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
        v = fields['dest_ranks'][e]
        if fields['capacities'][v] and rc.increments[e] == 0:
            zero_edges += 1
            internal_edges += labels[u] == labels[v]
assert len(sizes) == count
D = R/'experiments/real_zero_rc_scc_v1_2026-10-08'/name
D.mkdir(parents=True, exist_ok=False)
with (D/'components.bin').open('wb') as f:
    labels.tofile(f)
result = dict(nodes=len(nodes), enabled_nodes=sum(sizes.values()), components=count,
              nontrivial_components=sum(s>1 for s in sizes.values()),
              nodes_in_nontrivial_components=sum(s for s in sizes.values() if s>1),
              largest_component=max(sizes.values(), default=0),
              zero_edges=zero_edges, internal_zero_edges=internal_edges,
              partition_seconds_single=partition_seconds, scale=rc.scale,
              byteorder=sys.byteorder,
              scope='Zero congestion-price directed zero-RC partition census only; no physical path lifting, feedback or speed claim')
assert all(sha(p) == h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,result=result,
    files={str(D/'components.bin'):sha(D/'components.bin')}),indent=2)+'\n')
print(json.dumps(result,indent=2))
