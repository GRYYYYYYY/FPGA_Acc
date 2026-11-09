"""Full fresh-context parity on four archived moves, plus cache mutation isolation."""
import json,time,tempfile,sys
from pathlib import Path
from class_cached_rc_endpoint_session_v2 import load_endpoints,clear_cache,STATS
from class_cached_rc_endpoint_context_v1 import load_endpoints as reference
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/class_cached_rc_endpoint_session_cohort_v1_2026-10-08';D.mkdir(exist_ok=False)
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
clear_cache();rows=[];bindings={str(Path(__file__)):sha(Path(__file__)),str(R/'tools/class_cached_rc_endpoint_session_v2.py'):sha(R/'tools/class_cached_rc_endpoint_session_v2.py')}
bindings.update(closure([Path(__file__)]))
def node_equal(a,b):
 return a.tag==b.tag and dict(a.attrib)==dict(b.attrib) and len(a.children)==len(b) and all(node_equal(x,y) for x,y in zip(a.children,b))
for width,i in [(w,i) for w in (8,16,32) for i in range(4)]:
 ep=R/f'experiments/mux_budget_move_cohort_2026-10-06/w{width}_m{i}/target_endpoints.json';bindings[str(ep)]=sha(ep)
 bindings.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()})
 tick=time.perf_counter();a=load_endpoints(ep);cached=time.perf_counter()-tick
 tick=time.perf_counter();b=reference(ep);fresh=time.perf_counter()-tick
 assert a[:2]==b[:2] and a[3]==b[3] and a[5]==b[5]
 assert all(node_equal(x,y) for x,y in zip(a[2],b[2])) and len(a[2])==len(b[2])
 assert a[4].scale==b[4].scale and a[4].increments==b[4].increments
 assert a[4].rc.classes==tuple(b[4].rc.classes) and a[4].rc.switches==b[4].rc.switches
 assert list(a[4].rc.node_classes)==list(b[4].rc.node_classes)
 assert all(a[4].initial(n)==b[4].initial(n) for n in range(len(a[2])))
 bindings[str(a[0])]=sha(a[0]);rows.append(dict(width=width,move=i,session_seconds=cached,fresh_seconds=fresh,nodes=len(a[2]),edges=len(a[4].increments)))
 print(width,i,'complete context parity',cached,fresh,flush=True)
 if i==0:
  a[3]['capacities'][0]=0;a[4].increments[0]+=1;a[4].initial_by_class.clear();a[4].rc.switches.clear()
assert STATS['builds']==3 and STATS['hits']==9
cohort_stats=dict(STATS)
with tempfile.TemporaryDirectory(prefix='routecast-session-') as temp:
 epdata=json.loads(ep.read_text());epdata['graph_sha256']='0'*64;p=Path(temp)/'bad.json';p.write_text(json.dumps(epdata))
 try:load_endpoints(p)
 except ValueError:pass
 else:raise AssertionError('Stale graph admitted')
lru_rows=[]
for ep in (R/'experiments/mcnc_prospective_v1_2026-10-07/dsip/endpoints.json',R/'experiments/mux_budget_move_cohort_2026-10-06/w8_m0/target_endpoints.json'):
 bindings[str(ep)]=sha(ep)
 bindings.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()})
 tick=time.perf_counter();a=load_endpoints(ep);elapsed=time.perf_counter()-tick
 b=reference(ep)
 assert a[:2]==b[:2] and a[3]==b[3] and a[5]==b[5]
 assert all(node_equal(x,y) for x,y in zip(a[2],b[2])) and len(a[2])==len(b[2])
 assert a[4].scale==b[4].scale and a[4].increments==b[4].increments
 assert a[4].rc.classes==tuple(b[4].rc.classes) and a[4].rc.switches==b[4].rc.switches
 assert list(a[4].rc.node_classes)==list(b[4].rc.node_classes)
 assert all(a[4].initial(n)==b[4].initial(n) for n in range(len(a[2])))
 bindings[str(a[0])]=sha(a[0])
 lru_rows.append(dict(endpoint=str(ep),elapsed_seconds=elapsed,stats=dict(STATS)))
assert STATS==dict(builds=5,hits=9,evictions=2)

assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,cohort_stats=cohort_stats,lru_rows=lru_rows,stats=dict(STATS),isolated_mutations=True,stale_graph_rejected=True,scope='Same-process template reuse with all CSR/node/electrical/scale/increment/initial/query parity against fresh XML builds. Initial template freeze/clone and every input hash included in session clocks. Sequential same-case observations, no paired net gain or cross-process persistence claim.'),indent=2)+'\n')
print('Complete12 contexts passed; cohort stats',cohort_stats,'LRU stats',STATS)
