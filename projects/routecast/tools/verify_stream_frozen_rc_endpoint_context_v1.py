"""Full node/CSR/electrical/lattice parity, no workflow gain inference."""
import json,time
from pathlib import Path
from class_cached_rc_endpoint_context_v1 import load_endpoints as reference
from stream_frozen_rc_endpoint_context_v1 import load_endpoints as candidate
from cached_rr_endpoint_context_classes import freeze_node
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/stream_frozen_rc_endpoint_context_v1_2026-10-08';D.mkdir(exist_ok=False)
p=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json';cases=json.loads(p.read_text())['cases'];rows=[];bindings={str(p):sha(p)}
for w in (8,16,32):
 ep=Path(next(c['old'] for c in cases if c['width']==w))
 start=time.perf_counter();a=reference(ep);ref=time.perf_counter()-start
 start=time.perf_counter();b=candidate(ep);cand=time.perf_counter()-start
 assert a[:2]==b[:2] and a[5]==b[5]
 assert tuple(freeze_node(n) for n in a[2])==tuple(b[2])
 assert a[3]==b[3]
 assert a[4].scale==b[4].scale and a[4].increments==b[4].increments and a[4].initial_by_class==b[4].initial_by_class
 assert a[4].rc.node_classes==b[4].rc.node_classes and a[4].rc.classes==b[4].rc.classes and a[4].rc.switches==b[4].rc.switches and a[4].rc.cache==b[4].rc.cache
 try:b[2][0].attrib['type']='BROKEN'
 except TypeError:pass
 else:raise AssertionError('Mutable node')
 meta=json.loads(ep.read_text());bindings.update({str(ep):sha(ep),**{v['path']:v['sha256'] for v in meta['inputs'].values()}})
 row=dict(width=w,nodes=len(b[2]),edges=len(b[3]['edge_ids']),all_node_subtrees_csr_electrical_lattice_equal=True,reference_seconds=ref,candidate_seconds=cand);rows.append(row);print(row,flush=True)
assert all(sha(f)==h for f,h in bindings.items())
for n in ('verify_stream_frozen_rc_endpoint_context_v1.py','stream_frozen_rc_endpoint_context_v1.py','class_cached_rc_endpoint_context_v1.py','cached_rr_endpoint_context_classes.py','class_cached_integer_rc_v1.py','csr_exact_buffered_rc.py','path_rc.py','pre_route_endpoints.py'):
 f=R/'tools'/n;bindings[str(f)]=sha(f)
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Three full developed RR graphs, every immutable node subtree/CSR/class/switch/lattice/cache/query matches original reader. Single reference-first timing; reference clock excludes extra parity freeze, streaming includes immutable construction. No session/native/fullworkflow gain, heldout or budget admission claim.'),indent=2)+'\n')
