"""Complete physical route-import parity using immutable shared RR snapshot."""
import json,time,tempfile
from pathlib import Path
from dataclasses import FrozenInstanceError
from class_cached_rc_endpoint_context_v1 import load_endpoints
from immutable_endpoint_context_v1 import ImmutableEndpointContext
from load_complete_route_state_v1 import load_complete
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'immutable_adder_context_v1_2026-10-09';D.mkdir(exist_ok=False)
eps=[E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json']+[E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json' for i in range(1,4)]
start=time.perf_counter();owned=ImmutableEndpointContext.build(eps[0]);construction=time.perf_counter()-start;rows=[]
for step,ep in enumerate(eps):
 meta=json.loads(ep.read_text());route=E/f'adder_wire_guard_matched_cold_v5_2026-10-08/step_{step}/output.route'
 a=load_endpoints(ep);b=owned.load(ep);assert a[0].resolve()==b[0] and a[1]==b[1] and a[5]==b[5]
 assert all(tuple(a[3][k])==b[3][k] for k in a[3]) and a[4].scale==b[4].scale and tuple(a[4].increments)==b[4].increments
 x=load_complete(route,meta,a[2],a[3],a[4]);y=load_complete(route,meta,b[2],b[3],b[4]);assert x[:2]==y[:2] and x[2].wire==y[2].wire and x[2].occupancy==y[2].occupancy
 rows.append(dict(step=step,connections=len(y[0]),all_paths_delays_edges_wire_occupancy_equal=True))
negative=[]
def rejects(name,mutation):
 try:mutation()
 except (TypeError,AttributeError,FrozenInstanceError):negative.append(name)
 else:raise AssertionError(name+' mutation accepted')
rejects('capacity',lambda:owned.fields['capacities'].__setitem__(0,0))
rejects('node_attributes',lambda:owned.nodes[0].attrs.__setitem__('type','SINK'))
rejects('initial_delay',lambda:setattr(owned.rc,'initials',(0,)))
rejects('context_epoch',lambda:setattr(owned,'digest','0'*64))
with tempfile.TemporaryDirectory(prefix='routecast_immutable_') as tmp:
 meta=json.loads(eps[0].read_text());meta['graph_sha256']='0'*64;p=Path(tmp)/'endpoint.json';p.write_text(json.dumps(meta))
 try:owned.load(p)
 except ValueError:negative.append('wrong_epoch')
 else:raise AssertionError('epoch accepted')
out=dict(bindings={str(p):sha(p) for p in [*eps,Path(__file__),R/'tools/immutable_endpoint_context_v1.py',R/'tools/load_complete_route_state_v1.py']},rows=rows,negative_checks=negative,construction_seconds=construction,scope='All2064 native route imports match mutable reference exactly. Immutable Python snapshot, no peruse object scan; input hashes still fresh. Native ctypes CSR expects arrays and is not integrated; no whole workflow speedup.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
