"""Development full-Dijkstra capacity ablations, not legal native route publication."""
import heapq
from collections import Counter,defaultdict

def forecast(ctx,soft_capacity):
 graph,digest,nodes,f,rc,queries=ctx.context
 unions=defaultdict(set);parents=defaultdict(dict);ledger=Counter();records=[];events=[];failure=None
 for q in sorted(queries,key=lambda q:(q['net_id'],q['connection_id'])):
  net=q['net_id'];own=unions[net];source=q['source'];sink=q['sink']
  def allowed(n):return f['capacities'][n]>0 and (soft_capacity or (ledger.get(n,0)-int(n in own))<f['capacities'][n])
  costs={source:0} if allowed(source) else {};back={};heap=[(0,source)] if costs else [];expanded=0
  while heap:
   cost,u=heapq.heappop(heap)
   if costs[u]!=cost:continue
   expanded+=1
   if u==sink:break
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    dst=f['dest_ranks'][slot];eid=f['edge_ids'][slot]
    if not allowed(dst) or dst==source:continue
    if dst in parents[net] and parents[net][dst]!=(u,eid):continue
    value=cost+rc.increments[slot]*(1+(ledger.get(dst,0)-int(dst in own)))
    if dst not in costs or value<costs[dst]:costs[dst]=value;back[dst]=(u,eid,slot);heapq.heappush(heap,(value,dst))
  if sink not in costs:
   failure={'query':q,'status':'NO_PATH_UNDER_CAPACITY_AND_TREE_POLICY'};events.append({'query':q,'committed':False,'expanded':expanded});break
  n=sink;path=[];slots=[];used={sink};incoming={}
  while n!=source:
   u,eid,slot=back[n];incoming[n]=(u,eid);path.append(eid);slots.append(slot);n=u
   if n in used:raise ValueError('cyclic predecessor')
   used.add(n)
  path.reverse();slots.reverse();delay=rc.initial(source)+sum(rc.increments[s] for s in slots);parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);answer={'status':'FOUND','physical_edge_ids':path,'delay':delay,'cost':costs[sink]};records.append({**q,'mode':'SOFT_CAPACITY_FORECAST' if soft_capacity else 'HARD_CAPACITY_NO_BUDGET','answer':answer});events.append({'query':q,'committed':True,'expanded':expanded})
 overflow=sum(max(0,v-f['capacities'][n]) for n,v in ledger.items())
 return {'status':'COMPLETE_FORECAST' if failure is None else 'INCOMPLETE_FORECAST','records':records,'events':events,'ledger':dict(ledger),'failure':failure,'completed_connections':len(records),'required_connections':len(queries),'graph_sha256':digest,'scale':rc.scale,'overflow_units':overflow,'over_1ns_connections':sum(r['answer']['delay']>rc.scale//10**9 for r in records),'soft_capacity':soft_capacity,'scope':'No delay budget or label truncation; positive-capacity physical nodes only, consistent NET tree, exactRC*(1+otherNETdemand)cost. Forecast only, no native legal/quality or accepted state claim.'}
