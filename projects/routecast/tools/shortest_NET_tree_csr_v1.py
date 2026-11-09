"""Shared CSR lexicographic shortest-tree support; physical edge IDs are slots."""
import heapq

def prepare_csr(offsets,destination,costs,capacities,kinds,source,sinks):
 sinks=tuple(sorted(set(sinks)));n=len(capacities)
 assert n==len(kinds) and len(offsets)==n+1 and offsets[-1]==len(destination)==len(costs)
 assert 0<=source<n and kinds[source]=='SOURCE' and capacities[source]>0
 assert sinks and all(0<=s<n and kinds[s]=='SINK' and capacities[s]>0 for s in sinks)
 distance={source:(0,0)};parents={};queue=[(0,0,source)];pending=set(sinks);settled=0;scanned=0
 while queue:
  cost,hops,u=heapq.heappop(queue)
  if distance[u]!=(cost,hops):continue
  settled+=1;pending.discard(u)
  if not pending:break
  if kinds[u]=='SINK':continue
  for eid in range(offsets[u],offsets[u+1]):
   scanned+=1;v=destination[eid]
   if capacities[v]<=0 or kinds[v]=='SOURCE':continue
   candidate=(cost+costs[eid],hops+1);previous=distance.get(v)
   if previous is None or candidate<previous:
    distance[v]=candidate;parents[v]=[(u,eid)];heapq.heappush(queue,(*candidate,v))
   elif candidate==previous:parents[v].append((u,eid))
 if pending:raise ValueError('unreachable NET sink')
 support=set(sinks);work=list(sinks)
 while work:
  v=work.pop()
  for u,_ in parents.get(v,[]):
   if u not in support:support.add(u);work.append(u)
 assert source in support
 choices={v:tuple(sorted(parents[v])) for v in sorted(support-{source})}
 assert all(distance[u][1]+1==distance[v][1] for v,row in choices.items() for u,_ in row)
 return dict(source=source,sinks=sinks,choices=choices,distance={v:distance[v] for v in support},search_stats=dict(settled_nodes=settled,scanned_edges=scanned,discovered_nodes=len(distance)))
