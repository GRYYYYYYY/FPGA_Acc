"""Order-reversed full readonly-node construction boundary comparison."""
import gc,json,time
from pathlib import Path
from class_cached_rc_endpoint_context_v1 import load_endpoints as reference
from stream_frozen_rc_endpoint_context_v1 import load_endpoints as candidate
from cached_rr_endpoint_context_classes import freeze_node
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/frozen_context_boundary_comparison_v1_2026-10-08';D.mkdir(exist_ok=False)
p=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json';cases=json.loads(p.read_text())['cases'];bindings={str(p):sha(p)};rows=[]
for n in ('trial_frozen_context_boundary_comparison_v1.py','class_cached_rc_endpoint_context_v1.py','stream_frozen_rc_endpoint_context_v1.py','cached_rr_endpoint_context_classes.py','class_cached_integer_rc_v1.py','csr_exact_buffered_rc.py','path_rc.py','pre_route_endpoints.py'):
 f=R/'tools'/n;bindings[str(f)]=sha(f)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,widths=[8,16,32],orders=[['reference','candidate'],['candidate','reference']],scope='Both produce complete immutable node subtrees, CSR and exact integer electrical context; reference freeze included. Serial same process; OS caches not flushed. Session template serialization/clone, input generation and native workflow outside.'),indent=2)+'\n')
for w in (8,16,32):
 ep=Path(next(c['old'] for c in cases if c['width']==w));meta=json.loads(ep.read_text());bindings.update({str(ep):sha(ep),**{v['path']:v['sha256'] for v in meta['inputs'].values()}})
 for repeat,order in enumerate((('reference','candidate'),('candidate','reference'))):
  values={};times={}
  for arm in order:
   gc.collect();start=time.perf_counter()
   if arm=='reference':
    x=reference(ep);x=(x[0],x[1],tuple(freeze_node(n) for n in x[2]),*x[3:])
   else:x=candidate(ep)
   times[arm]=time.perf_counter()-start;values[arm]=x
  a=values['reference'];b=values['candidate']
  assert a[:4]==b[:4] and a[5]==b[5]
  assert a[4].scale==b[4].scale and a[4].increments==b[4].increments and a[4].initial_by_class==b[4].initial_by_class
  assert a[4].rc.node_classes==b[4].rc.node_classes and a[4].rc.classes==b[4].rc.classes and a[4].rc.switches==b[4].rc.switches and a[4].rc.cache==b[4].rc.cache
  row=dict(width=w,repeat=repeat,order=order,seconds=times,candidate_over_reference=times['candidate']/times['reference'],complete_fields_equal=True);rows.append(row);print(row,flush=True)
  del values,a,b,x
assert all(sha(f)==h for f,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Six order-reversed full-field comparisons at equal readonly-node construction boundary, including original recursive freeze. Single host process, no statistical confidence/OS-cache control. No session/fullnative workflow speedup or budget acceptance.'),indent=2)+'\n')
