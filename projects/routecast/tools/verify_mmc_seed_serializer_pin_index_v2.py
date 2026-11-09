"""Full frozen MMC seed output parity for indexed terminal lookup."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from shared_compact_native_inventory_v1 import Inventory
from serialize_whole_net_subset_pin_index_v2 import serialize_subset
D=R/'experiments/mmc_seed_serializer_pin_index_v2_2026-10-08';D.mkdir()
base=R/'experiments/ultraembedded_mmc_continuous_workflow_v3_2026-10-08'
proof=base/'verification.json';data=json.loads(proof.read_text())
assert data['all_cases_both_complete_arms_authenticated']
for path,digest in data['bindings'].items():assert sha(path)==digest,path
b=base/'seed';ep=b/'demand/mmc/endpoints.json';identity=b/'demand/mmc/identity.jsonl';native=b/'native/mmc';subset=native/'subset.json';place=native/'design.place'
graph=b/'rr/mmc/rr_graph.xml';reference=native/'seed.route';mapping=native/'bindings.json'
bindings={**closure([Path(__file__),R/'tools/serialize_whole_net_subset_pin_index_v2.py']),**{str(p):sha(p) for p in [proof,ep,identity,subset,place,graph,reference,mapping]}}
candidate=json.loads(subset.read_text());inv=Inventory(graph)
text,pins=serialize_subset(candidate,ep,identity,place,inv)
assert text.encode()==reference.read_bytes(),'complete route bytes mismatch'
assert pins==json.loads(mapping.read_text()),'complete pin bindings mismatch'
(D/'seed.route').write_text(text);(D/'bindings.json').write_text(json.dumps(pins)+'\n')
assert all(sha(k)==v for k,v in bindings.items())
result=dict(bindings=bindings,all_selected_connections=len(candidate['records']),all_selected_nets=len({x['net_id'] for x in candidate['records']}),complete_seed_route_bytes_and_all_pin_bindings_exact=True,scope='Full selected MMC seed, original endpoint/whole NET/identity ambiguity/physical parent/branch/graph checks retained. No runtime or whole workflow gain claim.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result['all_selected_connections'],result['all_selected_nets'],'FULL_SERIALIZATION_PARITY_PASS',flush=True)
