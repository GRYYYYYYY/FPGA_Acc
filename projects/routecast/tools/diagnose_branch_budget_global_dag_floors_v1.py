"""Fixed-local-delay full-DAG lower-bound diagnostic; original budgets remain immutable."""
import json
from fractions import Fraction as F
from collections import defaultdict,deque
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];C=R/'experiments/branch_budget_admission_census_v1_2026-10-08';vp=C/'verification.json';v=json.loads(vp.read_text());assert v['all_twelve_cases_independent_admission_pass'] and all(sha(f)==h for f,h in v['bindings'].items())
bindings={**v['bindings'],str(vp):sha(vp),str(Path(__file__)):sha(Path(__file__))};rows=[]
for case in v['rows']:
 w,i=case['width'],case['index'];ap=C/f'w{w}_m{i}_admission.json';admission=json.loads(ap.read_text());floor={str(x['connection_id']):F(x['minimum_seconds']) for x in admission['rows']}
 allocation=R/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';a=json.loads(allocation.read_text());tg=R/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mp=R/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json'
 assert sha(tg)==a['graph_sha256'] and sha(mp)==a['mapping_sha256'];mapping=json.loads(mp.read_text());assert mapping['timing_graph_sha256']==sha(tg)
 for p in (ap,allocation,tg,mp):bindings[str(p)]=sha(p)
 graph=json.loads(tg.read_text());edges=graph['edges'];adj=defaultdict(list);ind={int(n):0 for n in graph['nodes']}
 assert set(a['edge_connection_ids'])==set(mapping['external_edges'])
 for eid,e in edges.items():
  if e['disabled']:continue
  adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
 q=deque(n for n,d in ind.items() if d==0);order=[]
 while q:
  u=q.popleft();order.append(u)
  for sink,eid in adj[u]:
   ind[sink]-=1
   if not ind[sink]:q.append(sink)
 assert len(order)==len(ind);arrival={n:F(0) for n in order};parent={}
 for u in order:
  for sink,eid in adj[u]:
   if eid in a['edge_connection_ids']:
    cid=str(a['edge_connection_ids'][eid]);assert cid in floor;delay=floor[cid]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])
   else:delay=F(edges[eid]['max_delay_seconds'])
   candidate=arrival[u]+delay
   if candidate>arrival[sink]:arrival[sink]=candidate;parent[sink]=(u,eid)
 terminals=[int(n) for n,kind in graph['nodes'].items() if kind=='SINK'];critical=max(terminals,key=lambda n:arrival[n]);value=arrival[critical]*10**9;target=F(a['target_cpd_ns']);path=[];node=critical
 while node in parent:node,eid=parent[node];path.append(eid)
 path.reverse();rows.append(dict(width=w,index=i,original_connection_budget_admitted=case['admitted'],fixed_local_model_floor_cpd_ns=str(value),target_cpd_ns=str(target),fixed_local_model_global_floor_feasible=value<=target,critical_path_edge_ids=path))
D=R/'experiments/branch_budget_global_dag_floors_v1_2026-10-08';D.mkdir(exist_ok=False);assert all(sha(f)==h for f,h in bindings.items())
(D/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,complete_cases=12,rows=rows,scope='Full old timing DAG with all target independent certified RC floors and frozen old local/intracluster delay offsets; optimistic model only, not target native STA or joint physical capacity feasibility, no new budget vector or changed original protocol.'),indent=2)+'\n');print([(x['width'],x['index'],x['fixed_local_model_global_floor_feasible']) for x in rows])
