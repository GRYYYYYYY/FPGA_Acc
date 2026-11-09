"""Full fresh-context parity on four archived moves, plus cache mutation isolation."""
import json,time,tempfile
from pathlib import Path
from class_cached_rc_endpoint_session_v1 import load_endpoints,clear_cache,STATS
from class_cached_rc_endpoint_context_v1 import load_endpoints as reference
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/class_cached_rc_endpoint_session_v1_2026-10-08';D.mkdir(exist_ok=False)
clear_cache();rows=[];bindings={str(Path(__file__)):sha(Path(__file__)),str(R/'tools/class_cached_rc_endpoint_session_v1.py'):sha(R/'tools/class_cached_rc_endpoint_session_v1.py')}
def node_equal(a,b):
 return a.tag==b.tag and dict(a.attrib)==dict(b.attrib) and len(a.children)==len(b) and all(node_equal(x,y) for x,y in zip(a.children,b))
for i in range(4):
 ep=R/f'experiments/mux_budget_move_cohort_2026-10-06/w32_m{i}/target_endpoints.json';bindings[str(ep)]=sha(ep)
 tick=time.perf_counter();a=load_endpoints(ep);cached=time.perf_counter()-tick
 tick=time.perf_counter();b=reference(ep);fresh=time.perf_counter()-tick
 assert a[:2]==b[:2] and a[3]==b[3] and a[5]==b[5]
 assert all(node_equal(x,y) for x,y in zip(a[2],b[2])) and len(a[2])==len(b[2])
 assert a[4].scale==b[4].scale and a[4].increments==b[4].increments
 assert a[4].rc.classes==tuple(b[4].rc.classes) and a[4].rc.switches==b[4].rc.switches
 assert list(a[4].rc.node_classes)==list(b[4].rc.node_classes)
 assert all(a[4].initial(n)==b[4].initial(n) for n in range(len(a[2])))
 bindings[str(a[0])]=sha(a[0]);rows.append(dict(move=i,session_seconds=cached,fresh_seconds=fresh,nodes=len(a[2]),edges=len(a[4].increments)))
 if i==0:
  a[3]['capacities'][0]=0;a[4].increments[0]+=1;a[4].initial_by_class.clear();a[4].rc.switches.clear()
assert STATS['builds']==1 and STATS['hits']==3
with tempfile.TemporaryDirectory(prefix='routecast-session-') as temp:
 epdata=json.loads(ep.read_text());epdata['graph_sha256']='0'*64;p=Path(temp)/'bad.json';p.write_text(json.dumps(epdata))
 try:load_endpoints(p)
 except ValueError:pass
 else:raise AssertionError('Stale graph admitted')
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,stats=dict(STATS),isolated_mutations=True,stale_graph_rejected=True,scope='Same-process template reuse with all CSR/node/electrical/scale/increment/initial/query parity against fresh XML builds. Initial template freeze/clone and every input hash included in session clocks. Sequential same-case observations, no paired net gain or cross-process persistence claim.'),indent=2)+'\n')
print(rows,STATS)
