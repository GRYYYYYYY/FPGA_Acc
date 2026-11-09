"""Four-step full endpoint-context parity and negative epoch/mutation tests."""
import json,time,tempfile
from pathlib import Path
from class_cached_rc_endpoint_context_v1 import load_endpoints
from owned_endpoint_context_v1 import OwnedEndpointContext
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'owned_adder_endpoint_context_v1_2026-10-08';D.mkdir(exist_ok=False)
eps=[E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json']+[E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json' for i in range(1,4)]
tick=time.perf_counter();baseline=[load_endpoints(p) for p in eps];baseline_seconds=time.perf_counter()-tick
tick=time.perf_counter();owned=OwnedEndpointContext(eps[0]);actual=[owned.load(p) for p in eps];owned_seconds=time.perf_counter()-tick
for a,b in zip(baseline,actual):
 assert a[:2]==b[:2] and a[5]==b[5]
 assert set(a[3])==set(b[3]) and all(a[3][k]==b[3][k] for k in a[3])
 assert a[4].scale==b[4].scale and a[4].increments==b[4].increments
 import xml.etree.ElementTree as ET
 assert [ET.tostring(n) for n in a[2]]==[ET.tostring(n) for n in b[2]]
negative=[]
with tempfile.TemporaryDirectory(prefix='routecast_owned_context_') as tmp:
 m=json.loads(eps[0].read_text());m['graph_sha256']='0'*64;p=Path(tmp)/'wrong_epoch.json';p.write_text(json.dumps(m))
 try:owned.load(p)
 except ValueError:negative.append('wrong_epoch')
 else:raise AssertionError('epoch accepted')
fields=owned.context[3];old=fields['capacities'][0];fields['capacities'][0]=old+1
try:owned.load(eps[0])
except ValueError:negative.append('mutated_capacity')
else:raise AssertionError('mutation accepted')
fields['capacities'][0]=old;owned.load(eps[0]);assert len(negative)==2
out=dict(bindings={str(p):sha(p) for p in [*eps,Path(__file__),R/'tools/owned_endpoint_context_v1.py',R/'tools/class_cached_rc_endpoint_context_v1.py']},all4_full_context_parity=True,negative_checks=negative,baseline_component_seconds=baseline_seconds,owned_component_seconds=owned_seconds,scope='Sequential component observation including first preparation, peruse graph/input hashes and full mutation fingerprint. Not paired workflow speedup; no production routing integration yet.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
