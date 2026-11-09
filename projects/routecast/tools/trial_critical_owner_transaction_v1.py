"""Speculative complete-owner transactions; all staged query losses explicit and rollback atomic."""
import json,heapq,sys
from fractions import Fraction as F
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
B=R/'experiments/budget_occupied_branch_repair_v1_2026-10-08';bp=B/'complete_frame_verification_v2.json';proof=json.loads(bp.read_text());assert all(sha(f)==h for f,h in proof['bindings'].items())
base_receipt=json.loads((B/'receipt.json').read_text());base={int(cid):tuple(tuple(x) for x in path) for cid,path in base_receipt['state'].items()};base_delays={x['connection_id']:F(x['delay_seconds']) for x in proof['rows']}
cp=R/'experiments/critical_branch_constraint_ablation_v1_2026-10-08/blocking_owners.json';owners=json.loads(cp.read_text());assert owners['receipt_sha256']==sha(cp.parent/'receipt.json') and owners['verification_sha256']==sha(cp.parent/'verification.json')
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2);ep=Path(case['target']);graph,digest,nodes,f,rc,queries=load_endpoints(ep);byid={q['connection_id']:q for q in queries};budget=json.loads(Path(case['budget']).read_text());slotsource=[u for u in range(len(nodes)) for _ in range(f['row_offsets'][u],f['row_offsets'][u+1])]
D=R/'experiments/critical_owner_transaction_v1_2026-10-08';D.mkdir(exist_ok=False);bindings={**proof['bindings'],**closure([Path(__file__)]),str(bp):sha(bp),str(cp):sha(cp)}
plans=[]
for cid in (832,1892):
 owner=next(x['blocking_net_ids'] for x in owners['rows'] if x['connection_id']==cid);assert len(owner)==1
 released=sorted(q['connection_id'] for q in queries if q['net_id']==owner[0])
 for order in ('ASCENDING','DESCENDING'):plans.append(dict(critical=cid,owner=owner[0],released_connections=released,restore_order=released if order=='ASCENDING' else list(reversed(released)),order=order))
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,plans=plans,policy='Four fixed complete-owner transactions, critical first then all owner queries, original per-query budgets. Whole transaction rollback on any stage failure. Model/quality/native verification required before publication; no original state mutation.'),indent=2)+'\n')
def frame(state):
 unions=defaultdict(set);parents=defaultdict(dict)
 for cid,path in state.items():
  q=byid[cid];assert path[0]==(q['source'],None) and path[-1][0]==q['sink'] and len({n for n,s in path})==len(path)
  unions[q['net_id']].update(n for n,s in path)
  for (u,_),(v,s) in zip(path,path[1:]):
   assert v not in parents[q['net_id']] or parents[q['net_id']][v]==(u,s);parents[q['net_id']][v]=(u,s)
 ledger=Counter(n for union in unions.values() for n in union);assert all(c<=f['capacities'][n] for n,c in ledger.items());return unions,parents,ledger
rows=[]
for ordinal,plan in enumerate(plans):
 state=dict(base);released=set(plan['released_connections'])|{plan['critical']}
 for cid in released:del state[cid]
 events=[];success=True
 for cid in [plan['critical'],*plan['restore_order']]:
  q=byid[cid];net=q['net_id'];unions,parents,ledger=frame(state);outside=ledger.copy();outside.subtract(unions[net]);fixed=parents[net];source,sink=q['source'],q['sink']
  limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))/10**9*rc.scale;ceiling=limit.numerator//limit.denominator
  allowed=lambda u,i:outside[f['dest_ranks'][i]]<f['capacities'][f['dest_ranks'][i]] and (f['dest_ranks'][i] not in fixed or fixed[f['dest_ranks'][i]]==(u,f['switch_ids'][i]))
  assert outside[source]<f['capacities'][source];dist={source:rc.initial(source)};pred={};queue=[(dist[source],source)];settled=set();found=False
  while queue:
   value,u=heapq.heappop(queue)
   if value>ceiling:break
   if u in settled or dist[u]!=value:continue
   settled.add(u)
   if u==sink:found=True;break
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    if not allowed(u,slot):continue
    dst=f['dest_ranks'][slot];nd=value+rc.increments[slot]
    if nd<=ceiling and nd<dist.get(dst,nd+1):dist[dst]=nd;pred[dst]=slot;heapq.heappush(queue,(nd,dst))
  clip=dist[sink] if found else ceiling+1;pot={n:d for n,d in dist.items() if d<clip};assert pot.get(source,clip)==min(rc.initial(source),clip)
  for u,value in pot.items():
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    if allowed(u,slot):assert pot.get(f['dest_ranks'][slot],clip)<=value+rc.increments[slot]
  cert=D/f'plan{ordinal}_query{cid}.json';cert.write_text(json.dumps(dict(clip=clip,potentials={str(n):v for n,v in pot.items()}),separators=(',',':'))+'\n');bindings[str(cert)]=sha(cert)
  event=dict(connection_id=cid,status='STAGED' if found else 'NO_CONSTRAINED_BUDGET_PATH',budget_integer_ceiling=ceiling,certificate=str(cert),certificate_sha256=sha(cert))
  if found:
   slots=[];u=sink
   while u!=source:slot=pred[u];slots.append(slot);u=slotsource[slot]
   slots.reverse();edges=[f['edge_ids'][slot] for slot in slots];path=tuple([(source,None)]+[(f['dest_ranks'][slot],f['switch_ids'][slot]) for slot in slots]);assert rc.path(source,sink,edges)==dist[sink]<=ceiling
   state[cid]=path;frame(state);event.update(path=[list(x) for x in path],physical_edge_ids=edges,delay_integer=dist[sink])
  events.append(event)
  if not found:success=False;break
 assert set(base)==set(byid)
 if success:assert set(state)==set(base);frame(state)
 row=dict(plan=plan,events=events,transaction_complete=success,published=False,critical_delay_improved=success and F(events[0]['delay_integer'],rc.scale)<base_delays[plan['critical']],state={str(cid):[list(x) for x in path] for cid,path in (state if success else base).items()},scope='Completed candidate pending independent physical/budget/global/native checks' if success else 'Atomic whole transaction rollback; failed deterministic order does not prove joint infeasibility')
 rows.append(row);(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(ordinal,plan['critical'],plan['order'],'complete',success,'stages',len(events),flush=True)
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,scale=rc.scale,rows=rows,original_complete_connections=1929,base_state_unchanged=True),indent=2)+'\n')
