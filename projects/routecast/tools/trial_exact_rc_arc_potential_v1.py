"""Full positive-capacity RC potential certificate or explicit contradiction."""
import json,sys
from pathlib import Path
from collections import defaultdict,deque
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from exact_arc_potential_v1 import Potentials
name=sys.argv[1];assert name in ['xtea','8051','mmc']
P=R/'experiments/resident_radix_count_complete_v4_2026-10-08/protocol.json';protocol=json.loads(P.read_text())
assert all(sha(p)==h for p,h in protocol['bindings'].items())
endpoint=Path(next(x['endpoint'] for x in protocol['cases'] if x['name']==name))
bindings={**closure([Path(__file__)]),str(P):sha(P),str(endpoint):sha(endpoint)}
graph,digest,nodes,f,rc,queries=load_endpoints(endpoint);bindings[str(graph)]=digest
assert all(f['capacities'][q[k]]>0 for q in queries for k in ['source','sink'])
D=R/'experiments/exact_rc_arc_potential_v1_2026-10-08'/name;D.mkdir(parents=True,exist_ok=False)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scale=rc.scale,graph_sha256=digest,scope='Every directed arc whose source and destination both have positive capacity; all complete endpoint query terminals verified positive. Zero congestion-price integer buffered RC only. Constraint uses original physical arc ID; contradiction forest may traverse arcs backwards as algebra, never as a routing path.'),indent=2)+'\n')
uf=Potentials(len(nodes));forest=defaultdict(list);checked=0;conflict=None
for u in range(len(nodes)):
 if not f['capacities'][u]:continue
 for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
  v=f['dest_ranks'][slot]
  if not f['capacities'][v]:continue
  eid=f['edge_ids'][slot];cost=rc.increments[slot];checked+=1;status=uf.constrain(u,v,cost)
  if status=='merged':forest[u].append((v,eid,1));forest[v].append((u,eid,-1))
  elif status=='conflict':
   todo=deque([u]);previous={u:None}
   while todo and v not in previous:
    x=todo.popleft()
    for y,e,direction in forest[x]:
     if y not in previous:previous[y]=(x,e,direction);todo.append(y)
   assert v in previous;path=[];x=v
   while x!=u:before,e,direction=previous[x];path.append(dict(source=before,sink=x,physical_edge_id=e,direction=direction));x=before
   path.reverse();a,du=uf.find(u);b,dv=uf.find(v);assert a==b and dv-du!=cost
   conflict=dict(source=u,sink=v,physical_edge_id=eid,increment_integer=cost,forest_implied_increment_integer=dv-du,algebraic_forest_path=path);break
 if conflict:break
if conflict:
 result=dict(status='POTENTIAL_CONTRADICTION',checked_arcs_until_contradiction=checked,conflict=conflict)
else:
 potential=[];components=[]
 for n in range(len(nodes)):root,value=uf.find(n);components.append(root);potential.append(value)
 query_rows=[]
 for q in queries:
  assert components[q['source']]==components[q['sink']]
  delay=rc.initial(q['source'])+potential[q['sink']]-potential[q['source']]
  assert delay>=0;query_rows.append(dict(connection_id=q['connection_id'],source=q['source'],sink=q['sink'],endpoint_path_delay_integer=delay))
 (D/'potential.json').write_text(json.dumps(dict(potential=potential,components=components))+'\n')
 (D/'query_delays.json').write_text(json.dumps(query_rows)+'\n')
 result=dict(status='ALL_POSITIVE_CAPACITY_ARCS_POTENTIAL_PASS',checked_arcs=checked,original_nodes=len(nodes),original_arcs=len(f['edge_ids']),queries=len(query_rows),scope='Telescoping RC for every valid positive-capacity path, not proof of directed reachability, zero-price path selection, weighted-feedback objective, native pin legality or characterized physical timing.')
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,result=result,files={str(p):sha(p) for p in D.iterdir() if p.is_file()}),indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='conflict'},indent=2))
