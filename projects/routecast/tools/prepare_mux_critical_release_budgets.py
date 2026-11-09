"""Deterministic retained critical-NET expansion, no cold-route oracle."""
import json
from fractions import Fraction as F
from collections import defaultdict,deque
from pathlib import Path
from persistent_rc_context import PersistentRCContext
from online_conflict_core import shortest_delay
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_allfanin_budgets_2026-10-06';out=ROOT/'experiments/mux_critical_release_budgets_2026-10-06';out.mkdir();p=json.loads((base/'protocol.json').read_text());rows=[];last=None
(out/'protocol.json').write_text(json.dumps(dict(cases=p['cases'],base_receipt_sha256=sha(base/'receipt.json'),sources={str(f):sha(f) for f in (Path(__file__),ROOT/'tools/online_conflict_core.py')},policy='All12 fixed moves. If floor violates target, choose retained NET on deterministic maxplus critical path with largest sum path connection delays, NET ID tie. WholeNET relaxed exact Dijkstra floors, max4 added NETs. Initial changedwholeNET floor input preserved;24-step uniform interpolation. No cold-route trace input. Model/oldlocal hypotheses; no native STA or capacity realization.'),indent=2)+'\n')
for case in p['cases']:
 w,i=case['width'],case['index'];af=base/f'w{w}_m{i}.json';a=json.loads(af.read_text());tgf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';assert sha(tgf)==a['graph_sha256'] and sha(mf)==a['mapping_sha256'];tg=json.loads(tgf.read_text());m=json.loads(mf.read_text());ep=json.loads(Path(case['target']).read_text());queries={q['connection_id']:q for q in ep['connections']};floor={int(k):F(v) for k,v in a['floor_ns'].items()};expanded=set(a['affected']['affected_complete_net_connection_ids']);target=F(a['target_cpd_ns']);adj=defaultdict(list);ind={int(n):0 for n in tg['nodes']}
 for eid,e in tg['edges'].items():
  if not e['disabled']:adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
 queue=deque(sorted(n for n in ind if not ind[n]));order=[]
 while queue:
  u=queue.popleft();order.append(u)
  for v,eid in adj[u]:
   ind[v]-=1
   if not ind[v]:queue.append(v)
 assert len(order)==len(ind)
 def evaluate(b):
  arrival={n:F(0) for n in order};back={}
  for u in order:
   for v,eid in adj[u]:
    delay=b[a['edge_connection_ids'][eid]]+F(m['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in a['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9;value=arrival[u]+delay
    if value>arrival[v]:arrival[v]=value;back[v]=(u,eid)
  worst=max(sorted(int(n) for n,kind in tg['nodes'].items() if kind=='SINK'),key=lambda n:arrival[n]);path=[];n=worst
  while n in back:n,eid=back[n];path.append(eid)
  return arrival[worst],list(reversed(path))
 trace=[];added=[];certs={};value,path=evaluate(floor);reason=None
 while value>target and len(added)<4:
  contributions=defaultdict(lambda:F(0))
  for eid in path:
   cid=a['edge_connection_ids'].get(eid)
   if cid is not None and cid not in expanded:contributions[queries[cid]['net_id']]+=floor[cid]
  if not contributions:reason='NO_RETAINED_NET_ON_CRITICAL_PATH';break
  net=min(contributions,key=lambda n:(-contributions[n],n));before=value
  if last!=w:ctx=PersistentRCContext(case['target']);last=w
  else:ctx.bind_endpoints(case['target'])
  minima={};supported=True
  for cid,q in queries.items():
   if q['net_id']!=net:continue
   key=str(q['source'])
   if key not in certs:certs[key]=shortest_delay(ctx,q['source'],q['sink'],set())
   minimum=certs[key]['distances'].get(q['sink'])
   if minimum is None:supported=False;break
   minima[cid]=F(minimum*10**9,ctx.rc.scale)
  if not supported:reason='RELAXED_RELEASE_NET_UNREACHABLE';break
  prior_path=list(path);floor.update(minima);expanded.update(minima);added.append(net);value,path=evaluate(floor);trace.append(dict(net_id=net,selection_path=prior_path,contributions_ns={str(n):str(v) for n,v in contributions.items()},before_cpd_ns=str(before),after_cpd_ns=str(value),minima_ns={str(cid):str(v) for cid,v in minima.items()}))
 valid=value<=target and all(floor[cid]<=1 for cid in expanded);budget={};low=F(0)
 if valid:
  budget=dict(floor);high=F(1)
  for _ in range(24):
   mid=(low+high)/2;trial={cid:v+mid*(1-v) if cid in expanded else v for cid,v in floor.items()}
   if evaluate(trial)[0]<=target:budget=trial;low=mid
   else:high=mid
 status='CRITICAL_RELEASE_VECTOR_CONSTRUCTED' if valid else (reason or 'RELEASE_BOUND_OR_CAP_REJECTED');file=out/f'w{w}_m{i}.json';file.write_text(json.dumps(dict(status=status,base_sha256=sha(af),graph_sha256=sha(tgf),mapping_sha256=sha(mf),target_cpd_ns=str(target),trace=trace,added_nets=added,expanded_connection_ids=sorted(expanded),floor_ns={str(cid):str(v) for cid,v in floor.items()},model_floor_cpd_ns=str(value),budgets_ns={str(cid):str(v) for cid,v in budget.items()},model_budget_cpd_ns=str(evaluate(budget)[0]) if budget else None,interpolation=str(low),certificates=certs),indent=2)+'\n');row=dict(width=w,index=i,status=status,added_nets=added,floor_cpd_ns=float(value),sha256=sha(file));rows.append(row);print(row,flush=True)
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
