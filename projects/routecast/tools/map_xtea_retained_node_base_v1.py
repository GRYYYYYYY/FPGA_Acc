"""Map observed XTEA node costs, then independently rebuild XML and float bits."""
import json,sys,struct,math
from pathlib import Path
from fractions import Fraction
from collections import Counter
from array import array
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from audit_structural_node_base_v1 import audit
from load_design_routing_inputs_v1 import load
R=Path(__file__).resolve().parents[1]
P=R/'experiments/xtea_retained_native_inputs_v1_2026-10-13'
O=R/'experiments/xtea_retained_node_base_v1_2026-10-13';O.mkdir()
proof=P/'criticality/verification.json';v=json.loads(proof.read_text());assert v['nonignored_pin_keys_exactly_manifest'] and v['all_values_and_pin_identities_equal_v1']
bindings={**v['bindings'],str(proof):sha(proof),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items())
ep=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json'
graph,digest,nodes,f,rc,queries=load_endpoints(ep)
table=P/'indexed/indexed.tsv';rows=[x.split() for x in table.read_text().splitlines()];assert rows[0][0]=='G' and int(rows[0][1])==len(nodes)
indices={int(x[1]):x for x in rows if x[0]=='I'};assert len(indices)==int(rows[0][2])
expected=Counter();mapping={};types=['SOURCE','SINK','IPIN','OPIN','CHANX','CHANY']
for row in rows:
 if row[0]!='N':continue
 kind,index,count=map(int,row[1:]);x=indices[index];key=types[kind],int(x[2]);assert key not in mapping
 raw=struct.unpack('f',struct.pack('f',float(x[3])))[0];assert math.isfinite(raw) and raw>=0
 exact=Fraction(raw)*rc.scale;integer=-(-exact.numerator//exact.denominator);assert 0<=integer<2**64 and 0<=integer-exact<1
 mapping[key]=integer;expected[key]=count
values=array('Q');counts=Counter()
for i,node in enumerate(nodes):
 assert node.get('id')==str(i);seg=node.find('segment');key=node.get('type'),int(seg.get('segment_id')) if seg is not None else -1
 values.append(mapping[key]);counts[key]+=1
assert counts==expected and sum(expected.values())==len(nodes)
path=O/'node_base.u64';path.write_bytes(values.tobytes());bindings[str(path)]=sha(path)
assert all(sha(p)==h for p,h in bindings.items())
proof=O/'verification.json';proof.write_text(json.dumps(dict(bindings=bindings,scale=rc.scale,nodes=len(nodes),array_byteorder=sys.byteorder,all_original_node_ids_types_segments_and_native_group_counts_pass=True,ceil_error_less_than_one_RC_lattice_unit_per_entry=True,scope='Initialized XTEA native cost-index groups, full original XML node domain and exact additive RC lattice; no routing or QoR evidence.'),indent=2)+'\n')
independent=audit(graph,proof,rc.scale);assert independent==tuple(values)
loaded,cs,admitted=load(ep,proof,P/'criticality',len(nodes),rc.scale);assert loaded==tuple(values) and len(cs)==len(queries)
admitted.update(closure([Path(__file__)]));assert all(sha(p)==h for p,h in admitted.items())
(O/'independent_verification.json').write_text(json.dumps(dict(bindings=admitted,nodes=len(nodes),connections=len(cs),scale=rc.scale,independent_XML_and_float32_bit_rebuild_equal=True,design_input_bundle_admitted=True,scope='Exposed XTEA input correctness, independent base-cost rebuild and strict input loader admission; no second-design routing execution yet.'),indent=2)+'\n')
print('XTEA node base and independent audit PASS',len(nodes),len(cs),'scale',rc.scale,flush=True)
