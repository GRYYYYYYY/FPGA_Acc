"""Hard capacity mask and bounded weighted tree search; no occupancy mutations.

Existing owner support may retain existing pressure. Newly acquired nodes must
have a free slot in the owner-excluded snapshot. UNKNOWN preserves the tree.
"""
from fractions import Fraction
from weighted_budget_pareto_search_v1 import search
class ZeroBounds:
 def bound(self,target,budget):return self
 def get(self,node):return 0
class CapacityMask:
 def __init__(self,capacities,ledger,owner_nodes):
  self.capacities=tuple(capacities);self.n=len(self.capacities);self.owner=frozenset(owner_nodes)
  if any(type(v) is not int or v<0 for v in self.capacities):raise ValueError('capacity domain')
  if any(type(n) is not int or not 0<=n<self.n or self.capacities[n]<=0 for n in self.owner):raise ValueError('owner node domain')
  if any(type(n) is not int or not 0<=n<self.n or type(v) is not int or v<0 for n,v in ledger.items()):raise ValueError('ledger domain')
  if any(ledger.get(n,0)<1 for n in self.owner):raise ValueError('owner absent from ledger')
  self.blocked=frozenset(n for n,v in ledger.items() if n not in self.owner and v>=self.capacities[n])
 def __len__(self):return self.n
 def __getitem__(self,node):
  if type(node) is not int or not 0<=node<self.n:raise IndexError(node)
  return int(self.capacities[node]>0 and node not in self.blocked)
class Graph:
 def __init__(self,original,mask,max_labels=10000):
  if len(mask)!=original.n or type(max_labels) is not int or max_labels<1:raise ValueError('mask/limit domain')
  self.original=original;self.mask=mask;self.n=original.n;self.offsets=original.offsets;self.dest=original.dest;self.inc=original.inc;self.initial=original.initial;self.max_labels=max_labels;self.events=[]
  self.bounds=ZeroBounds()
 def tree(self,source):
  if type(source) is not int or not 0<=source<self.n or not self.mask[source]:raise ValueError('forbidden source')
  return Tree(self,source)
class Tree:
 def __init__(self,graph,source):
  self.graph=graph;self.source=source;self.n=graph.n;self.offsets=graph.offsets;self.dest=graph.dest;self.inc=graph.inc;self.initial=graph.initial;self.arrival={source:self.initial[source]};self.parents={}
 def expand(self,target,criticality,prices,raw_budget):
  g=self.graph
  if type(target) is not int or not 0<=target<self.n:raise ValueError('target')
  if not isinstance(criticality,Fraction) or not 0<=criticality<=1:raise ValueError('criticality')
  if type(raw_budget) is not int or raw_budget<0:raise ValueError('budget')
  if any(not g.mask[n] for n in self.arrival):raise ValueError('forbidden seeded tree node')
  bound=g.bounds.bound(target,raw_budget);result=search(self.offsets,self.dest,self.inc,g.mask,self.arrival,target,criticality,prices,raw_budget,bound,max_labels=g.max_labels);g.events.append(dict(target=target,budget=raw_budget,initial_arrivals=sorted(self.arrival.items()),**result))
  if result['status']!='FOUND':return dict(status=result['status'],committed=False)
  attach=result['join'];prefix=[];u=attach
  while u!=self.source:parent,edge=self.parents[u];prefix.append(edge);u=parent
  prefix.reverse();updates=[];seen=set(self.arrival);value=self.arrival[attach];u=attach
  for edge in result['path_slots']:
   if not self.offsets[u]<=edge<self.offsets[u+1]:raise ValueError('invalid result chain')
   v=self.dest[edge]
   if v in seen or not g.mask[v]:raise ValueError('forbidden/cyclic result')
   seen.add(v);value+=self.inc[edge];updates.append((v,u,edge,value));u=v
  assert u==target and value==result['raw']<=raw_budget
  p,q=criticality.numerator,criticality.denominator;assert result['objective_numerator']==p*value+(q-p)*sum(prices.get(v,0) for v,parent,edge,arrival in updates)
  for v,parent,edge,arrival in updates:self.parents[v]=parent,edge;self.arrival[v]=arrival
  return dict(status='COMMITTED',committed=True,raw=value,objective_numerator=result['objective_numerator'],objective_denominator=q,attach=attach,new_nodes=len(updates),path_slots=tuple(prefix)+tuple(result['path_slots']))
