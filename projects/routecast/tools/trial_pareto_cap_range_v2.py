"""Frozen cap ablation on three previously failed queries; all costs retained."""
import json,sys,time,heapq
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from source_binding_v2 import closure
from tree_floor_pareto_astar_predictor_v5 import predict
base=R/'experiments/mcnc_prospective_v1_2026-10-07';parent=R/'experiments/mcnc_bounded_owner_pareto_v3_2026-10-07';reference=R/'experiments/pareto_first_limit_astar_v1_2026-10-07';out=R/'experiments/pareto_cap_range_v2_2026-10-07';out.mkdir();inputs={};sources=closure([Path(__file__)])
for name in ('bigkey','dsip','misex3'):
 ep=base/name/'endpoints.json';inputs[str(ep)]=sha(ep);inputs.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()})
 for file in (parent/name/'candidate.json',parent/name/'floors.json',reference/name/'remaining_delay.json'):inputs[str(file)]=sha(file)
protocol=dict(inputs=inputs,sources=sources,caps_ns=[0.125,0.25,0.5,1.0],scope='Development component ablation on all three first LABEL_LIMIT queries. Fixed caps/order/budgets/10000labels. Independent historical exact distance used only for retrospective assertion, never supplied to search. No full cohort, native QoR or net gain claim.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for name in ('bigkey','dsip','misex3'):
 tick=time.perf_counter();graph,digest,nodes,f,rc,_=load_endpoints(base/name/'endpoints.json');context=time.perf_counter()-tick;c=json.loads((parent/name/'candidate.json').read_text());q=c['failure']['query'];floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads((parent/name/'floors.json').read_text())};spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes]
 tick=time.perf_counter();reverse=[[] for _ in nodes]
 for u in range(len(nodes)):
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][slot]].append((u,slot))
 reverse_seconds=time.perf_counter()-tick;work=out/name;work.mkdir();tests=[]
 for denominator in (8,4,2,1):
  cap=rc.scale//(10**9*denominator);tick=time.perf_counter();dist=[cap]*len(nodes);dist[q['sink']]=0;heap=[(0,q['sink'])];settled=0
  while heap:
   d,v=heapq.heappop(heap)
   if d!=dist[v]:continue
   settled+=1
   for u,slot in reverse[v]:
    if f['capacities'][u]<=0:continue
    nd=d+rc.increments[slot]
    if nd<dist[u]:dist[u]=nd;heapq.heappush(heap,(nd,u))
  build=time.perf_counter()-tick;rem=dict(enumerate(dist));tick=time.perf_counter();state=predict(f,rc,[q],floors,seed_records=c['records'],spans=spans,penalty=rc.scale//10**11,remaining_delays={q['sink']:rem});search_seconds=time.perf_counter()-tick
  # Reference is loaded AFTER construction/search, not an input to either.
  exact={int(k):v for k,v in json.loads((reference/name/'remaining_delay.json').read_text()).items()};assert all(dist[u]==min(exact.get(u,cap),cap) for u in range(len(nodes)))
  for u in range(len(nodes)):
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    if f['capacities'][u]>0 and f['capacities'][f['dest_ranks'][slot]]>0:assert dist[u]<=rc.increments[slot]+dist[f['dest_ranks'][slot]]
  old={r['connection_id']:r for r in c['records']};new={r['connection_id']:r for r in state['records']};assert all(new[k]==v for k,v in old.items())
  for rec in state['records']:assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer']
  file=work/f'cap_1over{denominator}.json';file.write_text(json.dumps(state)+'\n');tests.append(dict(cap_integer=cap,cap_ns=1/denominator,settled=settled,build_seconds=build,search_seconds=search_seconds,completed=state['completed_connections'],failure=state['failure'],expanded=state['expanded_nodes'],exact_capped_reference_pass=True,bellman_pass=True,retained_records_pass=True,path_rc_budget_pass=True,file=str(file),sha256=sha(file)));print(name,1/denominator,state['completed_connections'],state['failure'],flush=True)
 rows.append(dict(name=name,context_seconds=context,reverse_adjacency_seconds=reverse_seconds,tests=tests));(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
