"""Independent prefix-bit potential and attaining sink-path certificates."""
import json
from pathlib import Path
from collections import defaultdict,deque,Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/fresh_wire_contraction_global_v1_2026-10-08';cp=D/'topology_certificate.json';c=json.loads(cp.read_text());rp=D/'receipt.json';r=json.loads(rp.read_text());assert all(sha(f)==h for f,h in r['bindings'].items())
tgpath=R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json';ap=R/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json';tg=json.loads(tgpath.read_text());a=json.loads(ap.read_text());assert a['graph_sha256']==sha(tgpath)
edges={eid:e for eid,e in tg['edges'].items() if not e['disabled']};groups=defaultdict(set);incoming=defaultdict(list);adj=defaultdict(list);degree={int(n):0 for n in tg['nodes']};sinks={int(n) for n,k in tg['nodes'].items() if k=='SINK'}
for eid,e in edges.items():
 incoming[e['sink']].append(eid);adj[e['source']].append(eid);degree[e['sink']]+=1
 if eid in a['edge_connection_ids']:groups[a['edge_connection_ids'][eid]].add(eid)
queue=deque(sinks);reachable=set(sinks);suffix={}
while queue:
 n=queue.popleft()
 for eid in incoming[n]:
  u=edges[eid]['source']
  if u not in reachable:reachable.add(u);suffix[u]=eid;queue.append(u)
assert reachable==set(c['sink_reachable_nodes'])
queue=deque(n for n,v in degree.items() if not v);order=[]
while queue:
 u=queue.popleft();order.append(u)
 for eid in adj[u]:
  v=edges[eid]['sink'];degree[v]-=1
  if not degree[v]:queue.append(v)
assert len(order)==len(degree)
bits={int(n):int(value,16) for n,value in c['prefix_bits'].items()};indices={int(cid):value for cid,value in c['query_bit_indices'].items()};multiplicity={int(cid):k for cid,k in c['multiplicities'].items()}
assert set(bits)==set(order) and set(indices)==set(multiplicity)==set(groups) and set(indices.values())==set(range(len(groups)))
assert all(0<=x<(1<<len(groups)) for x in bits.values())
overlap=set();checks=0
for eid,e in edges.items():
 if e['sink'] not in reachable:continue
 assert bits[e['source']]&~bits[e['sink']]==0;checks+=1
 if eid in a['edge_connection_ids']:
  cid=a['edge_connection_ids'][eid];bit=1<<indices[cid];assert bits[e['sink']]&bit
  if bits[e['source']]&bit:overlap.add(cid)
assert overlap==set(c['repeated_query_ids']);witnesses=[]
for cid,group in groups.items():
 relevant=[eid for eid in group if edges[eid]['sink'] in reachable];k=multiplicity[cid]
 if not relevant:assert k==0;continue
 if cid not in overlap:
  assert k==1 and all(not bits[edges[eid]['source']]&(1<<indices[cid]) for eid in relevant)
  path=[relevant[0]];n=edges[path[-1]]['sink']
  while n not in sinks:eid=suffix[n];path.append(eid);n=edges[eid]['sink']
 else:
  count={n:0 for n in order};pred={}
  for u in order:
   for eid in adj[u]:
    v=edges[eid]['sink'];value=count[u]+int(eid in group)
    if value>count[v]:count[v]=value;pred[v]=eid
  n=max(sinks,key=lambda n:count[n]);assert count[n]==k;path=[]
  while n in pred:eid=pred[n];path.append(eid);n=edges[eid]['source']
  path.reverse()
 assert sum(eid in group for eid in path)==k and edges[path[-1]]['sink'] in sinks
 assert all(edges[left]['sink']==edges[right]['source'] for left,right in zip(path,path[1:]));witnesses.append(dict(connection_id=cid,k=k,timing_edge_ids=path))
assert all(sha(f)==h for f,h in r['bindings'].items())
out=dict(bindings={**r['bindings'],str(rp):sha(rp),str(cp):sha(cp),str(Path(__file__)):sha(Path(__file__))},all_static_query_multiplicity_bounds_and_attaining_paths_pass=True,queries=len(groups),multiplicity_histogram=dict(Counter(multiplicity.values())),prefix_bit_edge_inequality_checks=checks,repeated_query_ids=sorted(overlap),witnesses=witnesses,scope='Enabled static DAG/mapping certificate independent of delay/placement values. Nonrepeated query bits cannot occur twice on a sink path; repeated groups independently checked by count DP. Full sink paths attain every positive K. Does not change original budgets or prove native STA/equivalence/runtime gain.')
(D/'topology_verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k not in ('bindings','witnesses')},flush=True)
