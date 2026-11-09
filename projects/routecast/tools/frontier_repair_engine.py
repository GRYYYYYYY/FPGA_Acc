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

def repair_frontier(ctx,r,state=None):
 graph,digest,nodes,f,rc,queries=ctx.context
 ctx.reset()
 if state is not None:
  state.check_prior(ctx,r)
  slots,unions,parents,records=state.slots,state.unions,state.parents,state.records
 else:
  slots={f['edge_ids'][s]:(u,f['dest_ranks'][s]) for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};unions=defaultdict(set);parents=defaultdict(dict);records={q['connection_id']:q for q in r['records']}
  for record in r['records']:
   net=record['net_id'];unions[net].add(record['source'])
   for eid in record['answer']['physical_edge_ids']:u,v=slots[eid];unions[net].add(v);parents[net][v]=(u,eid)
 ledger=Counter(n for used in unions.values() for n in used) if state is None else state.ledger;assert dict(ledger)=={int(n):c for n,c in r['ledger'].items()};failed=r['failure']['query'];other={n:c-int(n in unions[failed['net_id']]) for n,c in ledger.items()};frontier=residual_frontier(f,failed['source'],failed['sink'],other);owners={n:sorted(net for net,used in unions.items() if n in used and net!=failed['net_id']) for n in frontier};blockers=sorted({net for nets in owners.values() for net in nets});removed=[q for q in r['records'] if q['net_id'] in blockers];released={net:sorted(unions[net]) for net in blockers}
 for net in blockers:
  ledger.subtract(unions[net]);del unions[net];del parents[net]
 ledger+=Counter()
 for q in removed:del records[q['connection_id']]
 queue=[failed]+[q for q in sorted(queries,key=lambda q:(q['net_id'],q['connection_id'])) if q['net_id'] in blockers]+[q for q in queries if q['connection_id']>=failed['connection_id'] and q['connection_id']!=failed['connection_id'] and q['net_id'] not in blockers];attempts=[];failure=None
 for q in queue:
  net=q['net_id'];other=dict(ledger)
  for n in unions[net]:other[n]-=1
  other={n:c for n,c in other.items() if c};answer=ctx.query(q['source'],q['sink'],rc.scale//10**9,other,max_labels=10000);attempts.append({'query':q,'answer':answer})
  if answer['status']!='FOUND':failure={'query':q,'status':answer['status']};break
  used={q['source']};node=q['source'];incoming={}
  for eid in answer['physical_edge_ids']:u,v=slots[eid];assert node==u;node=v;used.add(v);incoming[v]=(u,eid)
  assert node==q['sink'];conflicts=[n for n,p in incoming.items() if n in parents[net] and parents[net][n]!=p]
  if conflicts:failure={'query':q,'status':'MULTI_PARENT_REJECTED','nodes':conflicts};break
  assert q['connection_id'] not in records;parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);records[q['connection_id']]={**q,'mode':'NATIVE_DELAY_COST','answer':answer}
 return {'status':'COMPLETE_DIAGNOSTIC' if failure is None else 'INCOMPLETE_NOT_PUBLISHABLE','records':[records[k] for k in sorted(records)],'completed_connections':len(records),'required_connections':len(queries),'failure':failure,'attempts':attempts,'release':{'frontier_owners':owners,'blocker_NETs':blockers,'removed_connection_ids':[q['connection_id'] for q in removed],'released_unions':released},'ledger':dict(ledger),'graph_sha256':digest,'scale':rc.scale}

def repair_history(ctx,prior,state=None):
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
 ledger=Counter(n for ns in unions.values() for n in ns) if state is None else state.ledger;history=Counter();failed=prior['failure']['query'];pending=deque([failed]+[q for q in queries if q['connection_id'] not in records and q['connection_id']!=failed['connection_id']]);events=[];repairs=0;failure=None
 while pending:
  q=pending.popleft();net=q['net_id'];other={n:c-int(n in unions[net]) for n,c in ledger.items()};other={n:c for n,c in other.items() if c};answer=ctx.query(q['source'],q['sink'],rc.scale//10**9,other,max_labels=10000);event={'type':'QUERY','query':q,'answer':answer,'committed':False};events.append(event)
  if answer['status']=='UNREACHABLE' and repairs<4:
   reachable=set();stack=[]
   if other.get(q['source'],0)<f['capacities'][q['source']]:reachable.add(q['source']);stack.append(q['source'])
   while stack:
    u=stack.pop()
    for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
     n=f['dest_ranks'][s]
     if n not in reachable and other.get(n,0)<f['capacities'][n]:reachable.add(n);stack.append(n)
   if q['sink'] in reachable:failure={'query':q,'status':'CONNECTED_BUDGET_OR_SEARCH_FAILURE'};break
   frontier=sorted({f['dest_ranks'][s] for u in reachable for s in range(f['row_offsets'][u],f['row_offsets'][u+1]) if f['dest_ranks'][s] not in reachable}) if reachable else [q['source']]
   owners={n:sorted(k for k,ns in unions.items() if k!=net and n in ns) for n in frontier};blockers=sorted({k for ks in owners.values() for k in ks})
   if not blockers:failure={'query':q,'status':'NO_RELEASABLE_OWNER'};break
   removed=sorted(cid for cid,r in records.items() if r['net_id'] in blockers);released={k:sorted(unions[k]) for k in blockers}
   for k in blockers:ledger.subtract(unions[k]);del unions[k];del parents[k]
   ledger+=Counter()
   for cid in removed:del records[cid]
   history.update(frontier)
   ctx.set_history(history)
   events.append({'type':'RELEASE','failed_query':q,'frontier':frontier,'reachable':sorted(reachable),'owners':owners,'blocker_NETs':blockers,'removed_connection_ids':removed,'released_unions':released,'history_after':dict(history)});repairs+=1;pending=deque([q]+[x for x in sorted(queries,key=lambda x:(x['net_id'],x['connection_id'])) if x['net_id'] in blockers]+[x for x in pending if x['net_id'] not in blockers]);continue
  if answer['status']!='FOUND':failure={'query':q,'status':answer['status']};break
  node=q['source'];used={node};incoming={}
  for eid in answer['physical_edge_ids']:u,n=slots[eid];assert u==node;node=n;used.add(n);incoming[n]=(u,eid)
  assert node==q['sink'];conflicts=[n for n,p in incoming.items() if n in parents[net] and parents[net][n]!=p]
  if conflicts:failure={'query':q,'status':'MULTI_PARENT_REJECTED','nodes':conflicts};break
  assert q['connection_id'] not in records;parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);records[q['connection_id']]={**q,'mode':'NATIVE_HISTORY_DELAY_COST','answer':answer};event['committed']=True
 return {'status':'COMPLETE_DIAGNOSTIC' if failure is None else 'INCOMPLETE_NOT_PUBLISHABLE','records':[records[k] for k in sorted(records)],'completed_connections':len(records),'required_connections':len(queries),'failure':failure,'events':events,'repairs':repairs,'history':dict(history),'ledger':dict(ledger),'graph_sha256':digest,'scale':rc.scale}

