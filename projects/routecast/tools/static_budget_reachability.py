"""Exact integer-RC reachability within a fixed cap, no demand or label limit."""
import heapq

def within_budget(rows,dest,increments,capacities,source,initial,budget,targets):
 if not 0<=source<len(capacities) or initial<0 or budget<0:raise ValueError('invalid source/cap')
 targets=set(targets)
 if any(not 0<=n<len(capacities) for n in targets):raise ValueError('invalid target')
 dist={};queue=[];settled={};examined=0
 if capacities[source]>0 and initial<=budget:dist[source]=initial;queue=[(initial,source)]
 remaining=set(targets)
 while queue and remaining:
  value,node=heapq.heappop(queue)
  if node in settled or value!=dist[node]:continue
  settled[node]=value;remaining.discard(node)
  for i in range(rows[node],rows[node+1]):
   examined+=1;dst=dest[i];inc=increments[i]
   if inc<0:raise ValueError('negative arc delay')
   if capacities[dst]<=0 or dst in settled:continue
   new=value+inc
   if new<=budget and (dst not in dist or new<dist[dst]):dist[dst]=new;heapq.heappush(queue,(new,dst))
 return dict(target_minima={n:settled.get(n) for n in sorted(targets)},settled_nodes=len(settled),examined_edges=examined,all_targets_settled=not remaining)
