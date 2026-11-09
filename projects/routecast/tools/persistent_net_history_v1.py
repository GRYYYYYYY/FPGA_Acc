"""Full NET history generation using persistent graph/search/path certificates."""
from collections import Counter,defaultdict,deque
from pre_route_endpoints import sha

def generate(context,q,budgets,old):
 assert not context.closed and sha(context.graph)==context.digest
 assert set(old)==set(q)==set(budgets)
 inv=context.audit.inventory;rc=context.rc;search=context.search;length=context.length
 groups=defaultdict(list)
 for cid,item in q.items():groups[item['net_id']].append(cid)
 caps={n:int(cap) for n,(_,cap) in inv.physical.nodes.items()}
 edge={eid:arc for arc,eid in inv.physical.arcs.items()}
 def eligible(cid,path):
  if not path or path[0]!=[q[cid]['source'],None] or path[-1][0]!=q[cid]['sink']:return False
  try:delay,_,_=context.audit.certificate(path)
  except (AssertionError,KeyError,ValueError):return False
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
 state={};owners=defaultdict(set);events=[];rounds=[];failures={};history=defaultdict(Counter)
 for iteration in range(1024):
  if not queue:break
  net=queue.popleft();outside=Counter({n:len(ns) for n,ns in owners.items()})
  pending,queries,status=construct(net,outside);events.extend(queries);evicted=set()
  if pending is None:
   # Relax only external NET occupancy; preserve intra-NET parent and exact budgets.
   candidates=[];relaxed_status='NO_BOUNDED_ALTERNATIVE'
   terminals={q[cid][key] for cid in groups[net] for key in ('source','sink')}
   bans=[None]+[n for n,count in sorted(history[net].items(),key=lambda item:(-item[1],item[0])) if n not in terminals][:8]
   for ban in bans:
    constraints=Counter() if ban is None else Counter({ban:caps[ban]})
    alternative,queries,relaxed_status=construct(net,constraints)
    for event in queries:event['history_banned_node']=ban
    events.extend(queries)
    if alternative is not None:
     candidate_nodes={n for path in alternative.values() for n,s in path}
     blockers={n for n in candidate_nodes if len(owners[n])>=caps[n]}
     score=(sum(1+history[net][n] for n in blockers),len(blockers),sum(length.get(n,0) for n in candidate_nodes))
     candidates.append((score,alternative,ban))
   pending=min(candidates,key=lambda entry:entry[0])[1] if candidates else None
   if pending is None:
    failures[net]=dict(net=net,cid=groups[net][0],status=relaxed_status)
    rounds.append(dict(iteration=iteration,net=net,status='RELAXED_FAILURE',reason=relaxed_status));continue
   used={n for path in pending.values() for n,s in path}
   for n in used:
    if len(owners[n])>=caps[n]:evicted.update(owners[n])
   conflict_nodes={n for n in used if len(owners[n])>=caps[n]}
   for n in conflict_nodes:
    history[net][n]+=1
    for victim in owners[n]:history[victim][n]+=1
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

 selection=state if set(state)==set(q) else None
 missing={x['net_id'] for cid,x in q.items() if cid not in state}
 failed=[failures.get(net,dict(net=net,cid=groups[net][0],status='RETRY_BUDGET_EXHAUSTED')) for net in sorted(missing,key=str)]
 attempts=[dict(attempt=0,admitted_connections=len(state),failed_nets=failed,events=events,paths=state,rounds=rounds,history={str(net):dict(counts) for net,counts in history.items()})]
 assert sha(context.graph)==context.digest
 partial=attempts[0]['paths']
 context.audit.validate(partial,{cid:q[cid] for cid in partial},{cid:budgets[cid] for cid in partial})
 return dict(paths=selection,attempts=attempts)
