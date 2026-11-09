"""Exact fixed-local timing DAG lattice; no rounding or native STA equivalence."""
from fractions import Fraction as F
from math import lcm
from collections import defaultdict,deque

class ExactGlobalTiming:
 def __init__(self,tg,mapping,allocation,rc_scale,target,delays):
  self.edges={eid:e for eid,e in tg['edges'].items() if not e['disabled']}
  self.connection_ids=allocation['edge_connection_ids'];self.adj=defaultdict(list);self.groups=defaultdict(set)
  degree={int(n):0 for n in tg['nodes']};self.terminals={int(n) for n,k in tg['nodes'].items() if k=='SINK'}
  raw={}
  for eid,e in self.edges.items():
   self.adj[e['source']].append((e['sink'],eid));degree[e['sink']]+=1
   if eid in self.connection_ids:self.groups[self.connection_ids[eid]].add(eid);raw[eid]=F(mapping['external_edges'][eid]['old_local_offset_seconds'])
   else:raw[eid]=F(e['max_delay_seconds'])
  queue=deque(n for n,d in degree.items() if not d);self.order=[]
  while queue:
   u=queue.popleft();self.order.append(u)
   for v,eid in self.adj[u]:
    degree[v]-=1
    if not degree[v]:queue.append(v)
  assert len(self.order)==len(degree) and self.terminals
  # RC paths use rc_scale. Fixed local offsets, echo edges, and target are
  # included exactly, including signed local offsets; Python ints are unbounded.
  self.scale=lcm(rc_scale,F(target).denominator,*(x.denominator for x in raw.values()))
  self.base={eid:self.encode(value) for eid,value in raw.items()};self.target=self.encode(target)
  self.delays={cid:self.encode(value) for cid,value in delays.items()};self.multiplicities={};self.recompute()
 def encode(self,value):
  product=F(value)*self.scale
  if product.denominator!=1:raise ValueError('timing value outside exact lattice')
  return product.numerator
 def recompute(self):
  self.weights={eid:self.base[eid]+self.delays[self.connection_ids[eid]] if eid in self.connection_ids else self.base[eid] for eid in self.edges}
  self.forward={n:0 for n in self.order}
  for u in self.order:
   for v,eid in self.adj[u]:
    value=self.forward[u]+self.weights[eid]
    if value>self.forward[v]:self.forward[v]=value
  self.back={n:0 if n in self.terminals else None for n in self.order}
  for u in reversed(self.order):
   for v,eid in self.adj[u]:
    if self.back[v] is not None:
     value=self.weights[eid]+self.back[v]
     if self.back[u] is None or value>self.back[u]:self.back[u]=value
  self.cpd=max(self.forward[n] for n in self.terminals);assert self.cpd<=self.target
 def update(self,cid,value):
  self.delays[cid]=self.encode(value);self.recompute()
 def cpd_seconds(self):return F(self.cpd,self.scale)
 def safe_upper(self,cid,original_limit):
  relevant=[eid for eid in self.groups[cid] if self.back[self.edges[eid]['sink']] is not None]
  if not relevant:return original_limit,0,None
  if cid not in self.multiplicities:
   # A single enabled mapped edge reaching a SINK occurs at most once in a DAG,
   # and at least one sink path contains it. Multiple mapped edges use full DP.
   if len(self.groups[cid])==1:k=1
   else:
    count={n:0 for n in self.order}
    for u in self.order:
     for v,eid in self.adj[u]:
      value=count[u]+int(eid in self.groups[cid])
      if value>count[v]:count[v]=value
    k=max(count[n] for n in self.terminals)
   assert k>0;self.multiplicities[cid]=k
  k=self.multiplicities[cid];slack=min(self.target-self.forward[self.edges[eid]['source']]-self.weights[eid]-self.back[self.edges[eid]['sink']] for eid in relevant);assert slack>=0
  upper=min(F(original_limit),F(self.delays[cid]*k+slack,self.scale*k))
  return upper,k,F(slack,self.scale)
