"""Exact affected-node timing propagation on a fixed enabled DAG."""
import heapq
from collections import defaultdict
from exact_integer_global_timing_v2 import ExactGlobalTiming as Base

class ExactGlobalTiming(Base):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  self.rank={n:i for i,n in enumerate(self.order)};self.pred=defaultdict(list)
  for eid,e in self.edges.items():self.pred[e['sink']].append((e['source'],eid))
  self.update_work=[]
 def update(self,cid,value):
  encoded=self.encode(value);self.delays[cid]=encoded
  changed=[]
  for eid in self.groups[cid]:
   weight=self.base[eid]+encoded
   if self.weights[eid]!=weight:self.weights[eid]=weight;changed.append(eid)
  forward_seeds={self.edges[e]['sink'] for e in changed}
  queue=[(self.rank[n],n) for n in forward_seeds];heapq.heapify(queue);queued=set(forward_seeds);fw=0
  while queue:
   _,n=heapq.heappop(queue);queued.remove(n);fw+=1
   value=max([0]+[self.forward[u]+self.weights[e] for u,e in self.pred[n]])
   if value==self.forward[n]:continue
   self.forward[n]=value
   for v,_ in self.adj[n]:
    if v not in queued:heapq.heappush(queue,(self.rank[v],v));queued.add(v)
  back_seeds={self.edges[e]['source'] for e in changed}
  queue=[(-self.rank[n],n) for n in back_seeds];heapq.heapify(queue);queued=set(back_seeds);bw=0
  while queue:
   _,n=heapq.heappop(queue);queued.remove(n);bw+=1
   candidates=[0] if n in self.terminals else []
   candidates += [self.weights[e]+self.back[v] for v,e in self.adj[n] if self.back[v] is not None]
   value=max(candidates) if candidates else None
   if value==self.back[n]:continue
   self.back[n]=value
   for u,_ in self.pred[n]:
    if u not in queued:heapq.heappush(queue,(-self.rank[u],u));queued.add(u)
  self.cpd=max(self.forward[n] for n in self.terminals)
  self.update_work.append(dict(changed_edges=len(changed),forward_nodes=fw,backward_nodes=bw))
  assert self.cpd<=self.target
