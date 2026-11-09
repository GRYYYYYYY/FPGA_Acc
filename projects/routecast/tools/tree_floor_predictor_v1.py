"""Deterministic scalar additive-delay tree growth; no native route inputs."""
import heapq
from collections import Counter,defaultdict

def grouped_floor(fields,rc,source,sinks):
 remaining=set(sinks);dist={source:rc.initial(source)};queue=[(dist[source],source)];answer={}
 while queue and remaining:
  d,u=heapq.heappop(queue)
  if d!=dist[u]:continue
  if u in remaining:answer[u]=d;remaining.remove(u)
  for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
   v=fields['dest_ranks'][slot]
   if fields['capacities'][v]<=0:continue
   nd=d+rc.increments[slot]
   if v not in dist or nd<dist[v]:dist[v]=nd;heapq.heappush(queue,(nd,v))
 return answer

def predict(fields,rc,queries,floors,tree=True,floor_budget=True):
 offsets=fields['row_offsets'];dst=fields['dest_ranks'];caps=fields['capacities'];eids=fields['edge_ids'];owners=defaultdict(set);parents=defaultdict(dict);prefix=defaultdict(dict);ledger=Counter();records=[];failure=None;expanded=0
 for q in sorted(queries,key=lambda q:(q['net_id'],q['connection_id'])):
  net,src,sink=q['net_id'],q['source'],q['sink'];own=owners[net];par=parents[net];pd=prefix[net]
  if own and src not in pd:raise ValueError('multiple sources in one NET')
  floor=floors.get((src,sink));budget=max(rc.scale//10**9,(3*floor+1)//2) if floor_budget and floor is not None else rc.scale//10**9
  allowed=lambda n:ledger.get(n,0)-int(n in own)<caps[n]
  if not allowed(src):failure=dict(query=q,status='SOURCE_CAPACITY');break
  initial={n:d for n,d in pd.items() if d<=budget} if tree and own else {src:rc.initial(src)}
  dist=dict(initial);back={};queue=[(d,n) for n,d in initial.items()];heapq.heapify(queue);found=False
  while queue:
   d,u=heapq.heappop(queue)
   if d!=dist[u]:continue
   expanded+=1
   if u==sink:found=True;break
   for slot in range(offsets[u],offsets[u+1]):
    v=dst[slot]
    if (tree and v in own) or not allowed(v):continue
    nd=d+rc.increments[slot]
    if nd>budget:continue
    if v not in dist or nd<dist[v]:dist[v]=nd;back[v]=(u,eids[slot],slot);heapq.heappush(queue,(nd,v))
  if not found:failure=dict(query=q,status='NO_BUDGET_CAPACITY_PATH',floor_integer=floor,budget_integer=budget);break
  branch=[];node=sink
  while node in back:
   u,eid,slot=back[node];branch.append((u,node,eid,slot));node=u
  branch.reverse();join=node;path=[];seen={node}
  while node!=src:
   u,eid=par[node];assert u not in seen;seen.add(u);path.append(eid);node=u
  path.reverse();path.extend(eid for u,v,eid,slot in branch)
  incoming={v:(u,eid) for u,v,eid,slot in branch};conflicts=[v for v,p in incoming.items() if v in par and par[v]!=p]
  if conflicts:failure=dict(query=q,status='MULTI_PARENT_REJECTED',nodes=conflicts);break
  assert rc.path(src,sink,path)==dist[sink]<=budget
  used={src,join}|{v for u,v,eid,slot in branch};assert all(allowed(n) for n in used)
  # Prefix state includes every retained node, including older paths not used here.
  if not own:pd[src]=rc.initial(src)
  for u,v,eid,slot in branch:pd[v]=pd[u]+rc.increments[slot]
  par.update(incoming);ledger.update(used-own);own.update(used)
  records.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=path,delay=dist[sink]),budget_integer=budget,floor_integer=floor))
 return dict(status='COMPLETE_DIAGNOSTIC' if failure is None else 'INCOMPLETE_NOT_PUBLISHABLE',records=records,ledger=dict(ledger),completed_connections=len(records),required_connections=len(queries),failure=failure,expanded_nodes=expanded,tree=tree,floor_budget=floor_budget)
