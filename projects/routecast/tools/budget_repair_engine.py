"""Bounded budget-aware wholeNET repair using explicit persistent RC state.

The caller supplies an authenticated retained prefix. Returned incomplete state
is diagnostic and must not be published. Ledger state remains local to this call.
"""
import heapq
from collections import Counter,defaultdict,deque

def repair_budget(ctx,prior,max_repairs=4,max_labels=10000,state=None):
 if type(max_repairs) is not int or max_repairs<0:raise ValueError('nonnegative repair bound required')
 if type(max_labels) is not int or max_labels<1:raise ValueError('positive label bound required')
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
 ledger=Counter(n for ns in unions.values() for n in ns) if state is None else state.ledger;history=Counter({int(n):c for n,c in prior['history'].items()});
 ctx.set_history(history)
 failed=prior['failure']['query'];pending=deque([failed]+[q for q in queries if q['connection_id'] not in records and q['connection_id']!=failed['connection_id']]);events=[];repairs=0;failure=None
 while pending:
  q=pending.popleft();net=q['net_id'];other={n:c-int(n in unions[net]) for n,c in ledger.items()};other={n:c for n,c in other.items() if c};answer=ctx.query(q['source'],q['sink'],rc.scale//10**9,other,max_labels=max_labels);event={'type':'QUERY','query':q,'answer':answer,'committed':False};events.append(event)
  if answer['status']=='UNREACHABLE' and repairs<max_repairs:
   dist={q['source']:rc.initial(q['source'])};back={};heap=[(dist[q['source']],q['source'])]
   while heap:
    delay,u=heapq.heappop(heap)
    if delay!=dist[u]:continue
    if u==q['sink']:break
    for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
     n=f['dest_ranks'][slot]
     if f['capacities'][n]==0:continue
     nd=delay+rc.increments[slot]
     if n not in dist or nd<dist[n]:dist[n]=nd;back[n]=(u,f['edge_ids'][slot]);heapq.heappush(heap,(nd,n))
   if u!=q['sink']:
    failure={'query':q,'status':'EMPTY_DEMAND_DISCONNECTED'};break
   path=[];pathnodes={u};node=u
   while node!=q['source']:node,eid=back[node];path.append(eid);pathnodes.add(node)
   path=path[::-1]
   if delay>rc.scale//10**9:failure={'query':q,'status':'EMPTY_DEMAND_OVER_BUDGET'};break
   frontier=sorted(n for n in pathnodes if other.get(n,0)>=f['capacities'][n]);owners={n:sorted(k for k,ns in unions.items() if k!=net and n in ns) for n in frontier};blockers=sorted({k for ks in owners.values() for k in ks}|({net} if unions[net] else set()))
   if not blockers:failure={'query':q,'status':'NO_RELEASABLE_OWNER'};break
   removed=sorted(cid for cid,r in records.items() if r['net_id'] in blockers);released={k:sorted(unions[k]) for k in blockers}
   for k in blockers:ledger.subtract(unions[k]);del unions[k];del parents[k]
   ledger+=Counter()
   for cid in removed:del records[cid]
   history.update(frontier)
   ctx.set_history(history)
   events.append({'type':'RELEASE','failed_query':q,'frontier':frontier,'empty_path':path,'empty_delay_integer':delay,'owners':owners,'blocker_NETs':blockers,'removed_connection_ids':removed,'released_unions':released,'history_after':dict(history)});repairs+=1;pending=deque([q]+[x for x in queries if x['net_id']==net and x['connection_id']!=q['connection_id'] and net in blockers]+[x for x in sorted(queries,key=lambda x:(x['net_id'],x['connection_id'])) if x['net_id'] in blockers and x['net_id']!=net]+[x for x in pending if x['net_id'] not in blockers]);continue
  if answer['status']!='FOUND':failure={'query':q,'status':answer['status']};break
  node=q['source'];used={node};incoming={}
  for eid in answer['physical_edge_ids']:u,n=slots[eid];assert u==node;node=n;used.add(n);incoming[n]=(u,eid)
  assert node==q['sink'];conflicts=[n for n,p in incoming.items() if n in parents[net] and parents[net][n]!=p]
  if conflicts:failure={'query':q,'status':'MULTI_PARENT_REJECTED','nodes':conflicts};break
  assert q['connection_id'] not in records;parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);records[q['connection_id']]={**q,'mode':'NATIVE_HISTORY_DELAY_COST','answer':answer};event['committed']=True
 return {'status':'COMPLETE_DIAGNOSTIC' if failure is None else 'INCOMPLETE_NOT_PUBLISHABLE','records':[records[k] for k in sorted(records)],'completed_connections':len(records),'required_connections':len(queries),'events':events,'failure':failure,'repairs':repairs,'history':dict(history),'ledger':dict(ledger),'scale':rc.scale,'graph_sha256':digest}
