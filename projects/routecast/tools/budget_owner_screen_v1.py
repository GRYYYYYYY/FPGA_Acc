"""Necessary owner filter for a single extra release after baseline budget failure."""
import heapq,time
from collections import Counter

def screen(f,rc,q,forbidden,owners,budget,deadline=None):
 def check():
  if deadline is not None and time.perf_counter()>=deadline:raise TimeoutError('owner screen deadline')
 check();src,sink=q['source'],q['sink'];initial=rc.initial(src);n=len(f['capacities']);allowed=lambda u:u not in forbidden and f['capacities'][u]>0
 if initial>budget or not allowed(src) or not allowed(sink):return dict(candidates=[],envelope_nodes=[],saturated_nodes=[],forward={},reverse={},scope='No original-graph budget path.')
 reverse=[[] for _ in range(n)]
 for u in range(n):
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][slot]].append((u,slot))
 def distances(root,start,limit,backward):
  dist={root:start};heap=[(start,root)];pops=0
  while heap:
   d,u=heapq.heappop(heap)
   if d!=dist[u]:continue
   pops+=1
   if pops%1024==0:check()
   arcs=reverse[u] if backward else ((f['dest_ranks'][s],s) for s in range(f['row_offsets'][u],f['row_offsets'][u+1]))
   for v,s in arcs:
    if not allowed(v):continue
    nd=d+rc.increments[s]
    if nd<=limit and (v not in dist or nd<dist[v]):dist[v]=nd;heapq.heappush(heap,(nd,v))
  check();return dist
 forward=distances(src,initial,budget,False);back=distances(sink,0,budget-initial,True);envelope={u for u,d in forward.items() if u in back and d+back[u]<=budget};other=Counter(u for net,own in owners.items() if net!=q['net_id'] for u in own);saturated={u for u in envelope if other[u]>=f['capacities'][u]};candidates=sorted(net for net,own in owners.items() if net!=q['net_id'] and own.intersection(saturated));check()
 return dict(candidates=candidates,envelope_nodes=sorted(envelope),saturated_nodes=sorted(saturated),forward=forward,reverse=back,scope='Necessary single-extra-owner filter only if unchanged baseline has no budget path; not sufficient joint feasibility or native proof.')
