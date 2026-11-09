"""Sparse binary resource updates; exact spatial ranking still rebuilt."""
from fractions import Fraction as F
from direct_rank_objective_v1 import components

class State:
 def __init__(self,domain,points):
  domain.score(points)  # validate before constructing mutable state
  self.domain=domain;self.points=points.copy();n=len(points);self.count=[0]*(n+1);self.hits=[0]*(n+1);self.q=0;self.cross_sum=0;self.totals=[0]*len(domain.bin_keys)
  for i,p in enumerate(points):
   if p:self._change(i,1)
 def _change(self,i,delta):
  self.q+=delta;self.cross_sum+=delta*self.domain.centered_truth[i];j=i+1;n=len(self.points);hit=delta*int(i in self.domain.target_resource_top)
  while j<=n:self.count[j]+=delta;self.hits[j]+=hit;j+=j&-j
  for b in self.domain.memberships[i]:self.totals[b]+=delta
 def _prefix(self,tree,length):
  total=0
  while length:total+=tree[length];length-=length&-length
  return total
 def _first(self,k,ones):
  # Number of indices through kth selected bit (one or zero).
  lo,hi=1,len(self.points)
  while lo<hi:
   mid=(lo+hi)//2;count=self._prefix(self.count,mid);selected=count if ones else mid-count
   if selected>=k:hi=mid
   else:lo=mid+1
  return lo
 def update(self,changes):
  changes=list(changes);n=len(self.points)
  if len({i for i,p in changes})!=len(changes) or any(type(i) is not int or not 0<=i<n or type(p) is not int or p not in (0,1) for i,p in changes):raise ValueError('distinct valid indices and binary values required')
  for i,p in changes:
   delta=p-self.points[i]
   if delta:self._change(i,delta);self.points[i]=p
 def score(self):
  d=self.domain;n=len(self.points);cross=n*self.cross_sum;variance=n*self.q*(n-self.q)*d.truth_variance;rank=F(cross*abs(cross),variance) if variance else F(-2)
  if self.q>=d.rk:
   length=self._first(d.rk,True);hits=self._prefix(self.hits,length)
  else:
   length=self._first(d.rk-self.q,False);hits=self._prefix(self.hits,n)+sum(i<length for i in d.target_resource_top)-self._prefix(self.hits,length)
  spatial={key:F(value,capacity) for key,value,capacity in zip(d.bin_keys,self.totals,d.capacities)}
  return (rank,F(hits,d.rk),*components(spatial,d.spatial_truth,d.sk))
