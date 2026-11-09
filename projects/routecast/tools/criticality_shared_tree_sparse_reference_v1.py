"""Exact reference for ordered criticality-weighted shared-tree expansion.

Native initialized criticality is frozen input. This is not native RC Elmore
routing: raw electrical increments remain the existing additive proxy. Integer
objective is c*raw_arrival + (1-c)*new-node congestion. Previously owned tree
nodes incur no new congestion. Raw budgets gate commits; budget rejection is
not a proof that no feasible alternative exists.
"""
import heapq
from fractions import Fraction

class Tree:
 def __init__(self,fields,increments,initial,source):
  self.offsets=tuple(fields['row_offsets']);self.dest=tuple(fields['dest_ranks'])
  self.inc=tuple(increments);self.initial=tuple(initial);self.n=len(self.initial)
  if len(self.offsets)!=self.n+1 or self.offsets[0]!=0 or self.offsets[-1]!=len(self.dest) or len(self.inc)!=len(self.dest):raise ValueError('graph domain')
  if any(a>b for a,b in zip(self.offsets,self.offsets[1:])) or any(type(v) is not int or not 0<=v<self.n for v in self.dest):raise ValueError('invalid graph')
  if any(type(v) is not int or v<0 for v in self.inc+self.initial):raise ValueError('negative/noninteger raw cost')
  if type(source) is not int or not 0<=source<self.n:raise ValueError('source')
  self.source=source;self.arrival={source:self.initial[source]};self.parents={}
 def expand(self,target,criticality,congestion,raw_budget):
  if type(target) is not int or not 0<=target<self.n:raise ValueError('target')
  if not isinstance(criticality,Fraction) or not 0<=criticality<=1:raise ValueError('criticality must be exact Fraction')
  if not hasattr(congestion,'get'):raise ValueError('sparse congestion getter required')
  if type(raw_budget) is not int or raw_budget<0:raise ValueError('raw budget')
  p,q=criticality.numerator,criticality.denominator
  distance={u:p*d for u,d in self.arrival.items()};queue=[(d,u) for u,d in distance.items()];heapq.heapify(queue);previous={};visited=set()
  while queue:
   value,u=heapq.heappop(queue)
   if u in visited or value!=distance[u]:continue
   visited.add(u)
   if u==target:break
   for slot in range(self.offsets[u],self.offsets[u+1]):
    v=self.dest[slot]
    if v in self.arrival or v in visited:continue
    price=congestion.get(v,0)
    if type(price) is not int or price<0:raise ValueError('invalid sparse congestion')
    candidate=value+p*self.inc[slot]+(q-p)*price
    if candidate<distance.get(v,candidate+1):distance[v]=candidate;previous[v]=(u,slot);heapq.heappush(queue,(candidate,v))
  if target not in visited:return dict(status='UNREACHABLE',committed=False)
  new=[];u=target
  while u not in self.arrival:
   a,slot=previous[u];new.append((u,a,slot));u=a
  attach=u;raw=self.arrival[u]+sum(self.inc[slot] for _,_,slot in new)
  result=dict(status='COMMITTED' if raw<=raw_budget else 'RETAIN_RAW_BUDGET',committed=raw<=raw_budget,raw=raw,objective_numerator=distance[target],objective_denominator=q,attach=attach,new_nodes=len(new))
  if raw<=raw_budget:
   for v,a,slot in reversed(new):self.parents[v]=(a,slot);self.arrival[v]=self.arrival[a]+self.inc[slot]
  return result

class Graph:
 """One immutable graph snapshot shared by independent per-NET trees."""
 def __init__(self,fields,increments,initial):
  template=Tree(fields,increments,initial,0)
  self._snapshot={key:getattr(template,key) for key in ('offsets','dest','inc','initial','n')}
 def tree(self,source):
  if type(source) is not int or not 0<=source<self._snapshot['n']:raise ValueError('source')
  tree=Tree.__new__(Tree)
  for key,value in self._snapshot.items():setattr(tree,key,value)
  tree.source=source;tree.arrival={source:tree.initial[source]};tree.parents={}
  return tree
