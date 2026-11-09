"""Fixed three first-LABEL_LIMIT states, admissible original-input delay bound."""
import json,sys,time,heapq
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from source_binding_v2 import closure
from tree_floor_pareto_predictor_v4 import predict as baseline
from tree_floor_pareto_astar_predictor_v5 import predict as astar
base=R/'experiments/mcnc_prospective_v1_2026-10-07';parent=R/'experiments/mcnc_bounded_owner_pareto_v3_2026-10-07';out=R/'experiments/pareto_first_limit_astar_v1_2026-10-07';out.mkdir();inputs={};sources=closure([Path(__file__)])
for name in ('bigkey','dsip','misex3'):
 ep=base/name/'endpoints.json';inputs[str(ep)]=sha(ep);inputs.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()})
 for file in (parent/name/'candidate.json',parent/name/'floors.json'):inputs[str(file)]=sha(file)
protocol=dict(inputs=inputs,sources=sources,queries='Exactly all three first LABEL_LIMIT queries from frozen Pareto run; seed equals accepted partial snapshot',policy='Same budgets, spans, weight0.01ns and10000 labels, same retained-tree/owner constraints. Only add exact unrestricted positive-capacity remaining delay to sink as A* cost lower bound and delay-feasibility pruning. No bound retuning or native input.',scope='Post-outcome component comparison; not whole cohort, native proof or net gain. Full reverse lower-bound construction cost separately paid, no precomputation exclusion hidden.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for name in ('bigkey','dsip','misex3'):
 tick=time.perf_counter();graph,digest,nodes,f,rc,_=load_endpoints(base/name/'endpoints.json');context_s=time.perf_counter()-tick;c=json.loads((parent/name/'candidate.json').read_text());q=c['failure']['query'];assert c['failure']['status']=='LABEL_LIMIT';floors={(q['source'],q['sink']):q['minimum_integer'] for q in json.loads((parent/name/'floors.json').read_text())};spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];penalty=rc.scale//10**11;tick=time.perf_counter();reverse=[[] for _ in nodes]
 for u in range(len(nodes)):
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][s]].append((u,s))
 rem={q['sink']:0};heap=[(0,q['sink'])]
 while heap:
  d,v=heapq.heappop(heap)
  if d!=rem[v]:continue
  for u,s in reverse[v]:
   if f['capacities'][u]<=0:continue
   nd=d+rc.increments[s]
   if u not in rem or nd<rem[u]:rem[u]=nd;heapq.heappush(heap,(nd,u))
 # Check lower-bound feasibility over every reachable positive-capacity arc.
 for u in range(len(nodes)):
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][s]
   if v in rem and f['capacities'][u]>0:assert u in rem and rem[u]<=rc.increments[s]+rem[v]
 assert rc.initial(q['source'])+rem[q['source']]==floors[q['source'],q['sink']];bound_s=time.perf_counter()-tick;work=out/name;work.mkdir();(work/'remaining_delay.json').write_text(json.dumps(rem)+'\n');tests=[]
 for key,fn,kwargs in [('baseline',baseline,{}),('astar',astar,dict(remaining_delays={q['sink']:rem}))]:
  tick=time.perf_counter();state=fn(f,rc,[q],floors,seed_records=c['records'],spans=spans,penalty=penalty,**kwargs);elapsed=time.perf_counter()-tick;state.update(graph_sha256=digest,scale=rc.scale);file=work/(key+'.json');file.write_text(json.dumps(state)+'\n');tests.append(dict(kind=key,seconds=elapsed,completed=state['completed_connections'],failure=state['failure'],expanded=state['expanded_nodes'],sha256=sha(file)));print(name,key,state['completed_connections'],state['failure'],flush=True)
 assert tests[0]['failure']==c['failure']
 rows.append(dict(name=name,query=q,context_seconds=context_s,reverse_bound_and_consistency_seconds=bound_s,tests=tests,files={str(p):sha(p) for p in work.iterdir() if p.is_file()}));(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
