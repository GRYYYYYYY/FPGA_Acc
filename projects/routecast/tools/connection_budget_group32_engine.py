"""Capacity-frontier wholeNET release and bounded history continuation."""
from collections import Counter,defaultdict,deque

def residual_frontier(f,source,sink,other):
 reachable=set();pending=[]
 if other.get(source,0)<f["capacities"][source]:reachable.add(source);pending.append(source)
 while pending:
  u=pending.pop()
  for s in range(f["row_offsets"][u],f["row_offsets"][u+1]):
   n=f["dest_ranks"][s]
   if n not in reachable and other.get(n,0)<f["capacities"][n]:reachable.add(n);pending.append(n)
 if sink in reachable:raise ValueError("frontier repair requires disconnected residual graph")
 return sorted({f["dest_ranks"][s] for u in reachable for s in range(f["row_offsets"][u],f["row_offsets"][u+1]) if f["dest_ranks"][s] not in reachable}) if reachable else [source]

def repair_moved_history(ctx,prior,state=None):
 graph,digest,nodes,f,rc,queries=ctx.context
 ctx.reset()
 if state is not None:
  state.check_prior(ctx,prior)
  slots,unions,parents,records=state.slots,state.unions,state.parents,state.records
 else:
  slots={f['edge_ids'][s]:(u,f['dest_ranks'][s]) for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])}
  unions=defaultdict(set);parents=defaultdict(dict);records={q['connection_id']:q for q in prior['records']}
  for q in prior['records']:
   net=q['net_id'];unions[net].add(q['source'])
   for eid in q['answer']['physical_edge_ids']:u,n=slots[eid];unions[net].add(n);parents[net][n]=(u,eid)
 ledger=Counter(n for ns in unions.values() for n in ns) if state is None else state.ledger;history=Counter({int(n):c for n,c in prior['history'].items()});ctx.set_history(history);failed=prior['failure']['query'];pending=deque([failed]+[q for q in sorted(queries,key=lambda x:(NET_PRIORITY.get(x['net_id'],1000000),x['net_id'],x['connection_id'])) if q['connection_id'] not in records and q['connection_id']!=failed['connection_id']]);events=[];repairs=0;failure=None;conflict_groups=[]
 while pending:
  q=pending.popleft();net=q['net_id'];other={n:c-int(n in unions[net]) for n,c in ledger.items()};other={n:c for n,c in other.items() if c};answer=ctx.query(q['source'],q['sink'],BUDGETS.get(q['connection_id'],rc.scale//10**9),other,max_labels=10000);event={'type':'QUERY','query':q,'answer':answer,'committed':False};events.append(event)
  if answer['status']=='UNREACHABLE' and repairs<32:
   reachable=set();stack=[]
   if other.get(q['source'],0)<f['capacities'][q['source']]:reachable.add(q['source']);stack.append(q['source'])
   while stack:
    u=stack.pop()
    for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
     n=f['dest_ranks'][s]
     if n not in reachable and other.get(n,0)<f['capacities'][n]:reachable.add(n);stack.append(n)
   budget_frontier=None
   if q['sink'] in reachable:
    witness=ctx.query(q['source'],q['sink'],BUDGETS.get(q['connection_id'],rc.scale//10**9),{},max_labels=10000)
    if witness['status']!='FOUND':failure={'query':q,'status':'NO_BOUNDED_RELAXED_WITNESS','witness_status':witness['status']};break
    path_nodes={q['source']}
    for eid in witness['physical_edge_ids']:path_nodes.add(slots[eid][1])
    budget_frontier=sorted(n for n in path_nodes if other.get(n,0)>=f['capacities'][n])
    if not budget_frontier:failure={'query':q,'status':'NO_CAPACITY_BLOCKER_ON_WITNESS'};break
    events.append({'type':'BUDGET_WITNESS','query':q,'answer':witness,'blocked_nodes':budget_frontier})
   frontier=sorted({f['dest_ranks'][s] for u in reachable for s in range(f['row_offsets'][u],f['row_offsets'][u+1]) if f['dest_ranks'][s] not in reachable}) if reachable else [q['source']]
   if budget_frontier is not None:frontier=budget_frontier
   owners={n:sorted(k for k,ns in unions.items() if k!=net and n in ns) for n in frontier};blockers=sorted({k for ks in owners.values() for k in ks})
   if not blockers:failure={'query':q,'status':'NO_RELEASABLE_OWNER'};break
   direct_blockers=list(blockers);group={net,*blockers}
   # Merge only conflicts already observed in this candidate.
   merged=[]
   for old_group in conflict_groups:
    if group & old_group:group.update(old_group)
    else:merged.append(old_group)
   if len(group)>16:
    failure={'query':q,'status':'CONFLICT_GROUP_LIMIT','group_NETs':sorted(group),'limit':16};break
   conflict_groups=merged+[group]
   blockers=sorted(group)
   removed=sorted(cid for cid,r in records.items() if r['net_id'] in group);released={k:sorted(unions[k]) for k in blockers}
   events.append({'type':'CONFLICT_GROUP','failed_query':q,'direct_blocker_NETs':direct_blockers,'group_NETs':blockers,'limit':16})
   for k in blockers:ledger.subtract(unions[k]);del unions[k];parents.pop(k,None)
   ledger+=Counter()
   for cid in removed:del records[cid]
   history.update(frontier)
   ctx.set_history(history)
   events.append({'type':'RELEASE','failed_query':q,'frontier':frontier,'reachable':sorted(reachable),'owners':owners,'blocker_NETs':blockers,'removed_connection_ids':removed,'released_unions':released,'history_after':dict(history)});repairs+=1;pending=deque([x for x in sorted(queries,key=lambda x:(NET_PRIORITY.get(x['net_id'],1000000),x['net_id'],x['connection_id'])) if x['net_id'] in blockers]+[x for x in pending if x['net_id'] not in blockers]);continue
  if answer['status']!='FOUND':failure={'query':q,'status':answer['status']};break
  node=q['source'];used={node};incoming={}
  for eid in answer['physical_edge_ids']:u,n=slots[eid];assert u==node;node=n;used.add(n);incoming[n]=(u,eid)
  assert node==q['sink'];conflicts=[n for n,p in incoming.items() if n in parents[net] and parents[net][n]!=p]
  if conflicts:failure={'query':q,'status':'MULTI_PARENT_REJECTED','nodes':conflicts};break
  assert q['connection_id'] not in records;parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);records[q['connection_id']]={**q,'mode':'NATIVE_HISTORY_DELAY_COST','answer':answer};event['committed']=True
 return {'status':'COMPLETE_DIAGNOSTIC' if failure is None else 'INCOMPLETE_NOT_PUBLISHABLE','records':[records[k] for k in sorted(records)],'completed_connections':len(records),'required_connections':len(queries),'failure':failure,'events':events,'repairs':repairs,'history':dict(history),'ledger':dict(ledger),'graph_sha256':digest,'scale':rc.scale}


NET_PRIORITY={}

BUDGETS={}
