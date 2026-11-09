"""Full independent XML adapter parity and exact archived seed serialization."""
import json, sys, time
from pathlib import Path
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from shared_compact_native_inventory_v1 import Inventory as Original
from resident_native_inventory_v2 import Inventory as Candidate
from serialize_whole_net_subset_pin_index_v2 import serialize_subset

receipt_path = R/'experiments/xtea_seed_selection_native_routes_v1_2026-10-09/receipt.json'
receipt = json.loads(receipt_path.read_text())
for section in ['bindings','files']:
    assert all(sha(p)==h for p,h in receipt[section].items())
bindings = {**closure([Path(__file__)]), str(receipt_path):sha(receipt_path)}
epfile = next(Path(p) for p in receipt['bindings'] if p.endswith('/endpoints.json'))
ep = json.loads(epfile.read_text())
bindings.update({str(epfile):sha(epfile), **{v['path']:v['sha256'] for v in ep['inputs'].values()}})
tick = time.perf_counter()
graph,digest,nodes,fields,rc,queries = load_endpoints(epfile)
load_seconds = time.perf_counter()-tick
tick = time.perf_counter();old = Original(graph);old_seconds = time.perf_counter()-tick
tick = time.perf_counter();new = Candidate(graph,digest,nodes,fields);new_seconds = time.perf_counter()-tick
assert len(old.nodes)==len(new.nodes) and len(old.edges)==len(new.edges)
for node in old.nodes:
    assert old.nodes[node] == new.nodes[node]
    assert old.graph.nodes[node].capacity == new.graph.nodes[node].capacity
for eid in range(len(old.edges)):
    assert old.edges[eid] == new.edges[eid]
rows=[]
for policy in ['connection_count','connection_per_channel_span']:
    subset = R/f'experiments/xtea_seed_selection_order_v1_2026-10-09/{policy}.json'
    expected = receipt_path.parent/policy
    bindings[str(subset)] = sha(subset)
    candidate=json.loads(subset.read_text())
    tick=time.perf_counter()
    text,pins=serialize_subset(candidate,epfile,Path(ep['inputs']['native_identity']['path']),Path(ep['inputs']['place']['path']),new)
    seconds=time.perf_counter()-tick
    assert text.encode()==(expected/'seed.route').read_bytes()
    assert json.loads(json.dumps(pins))==json.loads((expected/'bindings.json').read_text())
    rows.append(dict(policy=policy,connections=len(pins),seconds=seconds))
assert all(sha(p)==h for p,h in bindings.items())
out=dict(bindings=bindings,all_original_XML_nodes_and_edges_equal=True,
         both_archived_seed_bytes_and_pin_bindings_equal=True,nodes=len(new.nodes),edges=len(new.edges),
         resident_model_context_load_seconds=load_seconds,original_extra_XML_inventory_seconds=old_seconds,
         candidate_resident_adapter_seconds=new_seconds,serialization=rows,
         scope='Current-arm resident model state only; no historical graph reuse. Full independent original XML comparison and full retained NET seed bytes. Shared adapter is not itself an independent XML audit. Single local XTEA development observation, no MMC or complete workflow savings, native admission, heldout or silicon claim.')
D=R/'experiments/xtea_resident_native_inventory_v2_2026-10-09';D.mkdir()
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
