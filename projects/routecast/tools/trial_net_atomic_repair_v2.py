"""Bounded whole-NET admission from actual old state; no CNF or target routes."""
import json,time
from collections import Counter,defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from unified_rr_audit_inventory_v2 import read
from native_bounded_wire_search_v1 import NativeBoundedSearch
from native_resume_prototype.source_binding_v2 import closure

R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'net_atomic_repair_v2_2026-10-09';D.mkdir(exist_ok=False)
start=time.perf_counter();bindings=closure([Path(__file__)])
base=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json'
ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json'
bp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_1_budgets.json'
op=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_0_state.json'
g,h,nodes,fields,rc,_=load_endpoints(base);inv=read(g,h)
for p in (base,ep,bp,op,g):bindings[str(p)]=sha(p)
q={x['connection_id']:x for x in json.loads(ep.read_text())['connections']}
budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())}
old={int(c):p for c,p in json.loads(op.read_text())['state'].items()}
groups=defaultdict(list)
for cid,item in q.items():groups[item['net_id']].append(cid)
length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
caps={n:int(cap) for n,(_,cap) in inv.physical.nodes.items()}
edge={eid:arc for arc,eid in inv.physical.arcs.items()}
search=NativeBoundedSearch(rc,length);bindings.update(search.bindings)

def eligible(cid,path):
 if not path or path[0]!=[q[cid]['source'],None] or path[-1][0]!=q[cid]['sink']:return False
 if len(set(n for n,s in path))!=len(path):return False
 r,c=inv.classes[inv.node_classes[path[0][0]]];delay=r*c/2
 for (u,_),(v,s) in zip(path,path[1:]):
  if inv.arc_multiplicities.get((u,v,s))!=1:return False
  r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td
 return delay<=budgets[cid]

def construct(net,outside):
 kept=set();parents={};pending={};events=[]
 for cid in sorted(groups[net]):
  path=old[cid]
  compatible=eligible(cid,path) and all(outside[n]<caps[n] for n,s in path)
  compatible=compatible and all(v not in parents or parents[v]==(u,s) for (u,_),(v,s) in zip(path,path[1:]))
  if not compatible:
   if outside[q[cid]['source']]>=caps[q[cid]['source']]:return None,events,'SOURCE_CAPACITY_BLOCKED'
   scaled=budgets[cid]*rc.scale
   result=search.query(q[cid]['source'],q[cid]['sink'],scaled.numerator//scaled.denominator,outside,kept,parents,100000,sum(length.values())+1)
   events.append(dict(cid=cid,**result))
   if result['status']!='FOUND':return None,events,result['status']
   path=[[q[cid]['source'],None]]
   for eid in result['physical_edge_ids']:
    u,v,s=edge[eid];assert u==path[-1][0];path.append([v,s])
  assert eligible(cid,path) and all(outside[n]<caps[n] for n,s in path)
  for (u,_),(v,s) in zip(path,path[1:]):
   assert v not in parents or parents[v]==(u,s);parents[v]=(u,s)
  kept.update(n for n,s in path);pending[cid]=path
 return pending,events,'FOUND'

from collections import deque
queue=deque(sorted(groups,key=lambda net:(-len(groups[net]),str(net))))
state={};owners=defaultdict(set);events=[];rounds=[];failures={}
for iteration in range(1024):
 if not queue:break
 net=queue.popleft();outside=Counter({n:len(ns) for n,ns in owners.items()})
 pending,queries,status=construct(net,outside);events.extend(queries);evicted=set()
 if pending is None:
  # Relax only external NET occupancy; preserve intra-NET parent and exact budgets.
  pending,queries,relaxed_status=construct(net,Counter());events.extend(queries)
  if pending is None:
   failures[net]=dict(net=net,cid=groups[net][0],status=relaxed_status)
   rounds.append(dict(iteration=iteration,net=net,status='RELAXED_FAILURE',reason=relaxed_status));continue
  used={n for path in pending.values() for n,s in path}
  for n in used:
   if len(owners[n])>=caps[n]:evicted.update(owners[n])
  # Whole NET release, then atomic whole NET admission. No partial branch release.
  for victim in sorted(evicted,key=str):
   removed=[cid for cid in state if q[cid]['net_id']==victim]
   victim_nodes={n for cid in removed for n,s in state[cid]}
   for n in victim_nodes:owners[n].remove(victim)
   for cid in removed:del state[cid]
   if victim not in queue:queue.append(victim)
 for cid,path in pending.items():
  assert cid not in state
  for n,s in path:assert len(owners[n])<caps[n] or net in owners[n]
 state.update(pending)
 for path in pending.values():
  for n,s in path:owners[n].add(net)
 failures.pop(net,None)
 rounds.append(dict(iteration=iteration,net=net,status='ADMITTED',evicted_nets=sorted(evicted,key=str),admitted_connections=len(state)))
 if iteration%100==0:print(rounds[-1],flush=True)
selection=state if set(state)==set(q) else None
missing={x['net_id'] for cid,x in q.items() if cid not in state}
failed=[failures.get(net,dict(net=net,cid=groups[net][0],status='RETRY_BUDGET_EXHAUSTED')) for net in sorted(missing,key=str)]
attempts=[dict(attempt=0,admitted_connections=len(state),failed_nets=failed,events=events,paths=state,rounds=rounds)]
search.close()
result=D/'result.json';result.write_text(json.dumps(dict(paths=selection,attempts=attempts),indent=2)+'\n');bindings[str(result)]=sha(result)
assert all(sha(p)==digest for p,digest in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,status='FOUND_REQUIRES_INDEPENDENT_FULL_GATES' if selection else 'NO_COMPLETE_SELECTION',component_seconds=time.perf_counter()-start,scope='Fresh bounded 1024 NET admissions; 100000 labels/query; external occupancy relaxed only to identify whole NET evictions. No impossibility claim, native/canonical final gates pending; positive-control budgets.'),indent=2)+'\n')
print(dict(admitted_connections=len(state),failed_nets=len(failed),iterations=len(rounds),component_seconds=time.perf_counter()-start),flush=True)
