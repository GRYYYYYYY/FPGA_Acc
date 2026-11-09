"""Separate optimization objective from exact original raw-delay outputs."""
from types import SimpleNamespace
from array import array
from lazy_wide_cost_search_bridge_v2 import Search as Backend, intern_objective_increments

class Search:
 def __init__(self,fields,rc,binary,node_base):
  self.closed=False;self.prepared=False
  self.fields={k:(tuple(v) if k=='capacities' else memoryview(array('Q',v).tobytes()).cast('Q')) for k,v in fields.items()};n=len(fields['capacities'])
  self.initial=tuple(rc.initial(u) for u in range(n));self.raw_inc=tuple(rc.increments);self.base=tuple(node_base)
  if len(self.base)!=n or len(self.raw_inc)!=len(fields['dest_ranks']):raise ValueError('cost domain mismatch')
  def valid(values):return all(type(v) is int and 0<=v<2**120 for v in values)
  if not valid(self.initial+self.raw_inc+self.base):raise ValueError('invalid integer costs')
  self.objective_inc=intern_objective_increments(self.raw_inc,self.fields['dest_ranks'],self.base)
  if not valid(self.objective_inc):raise ValueError('combined increment overflow')
  self.backends=[]
  try:
   for inc in [self.raw_inc,self.objective_inc]:self.backends.append(Backend(self.fields,SimpleNamespace(increments=inc,initial=self.initial.__getitem__),binary))
  except Exception:self.close();raise
 def prepare(self,prices,weight,*,structural=True):
  if self.closed:raise RuntimeError('closed search')
  if type(structural) is not bool:raise ValueError('invalid structural mode')
  values=tuple(prices.get(u,0) for u in range(len(self.base)))
  if type(weight) is not int or not 0<=weight<2**120 or any(type(v) is not int or not 0<=v<2**120 for v in values):raise ValueError('invalid prices or weight')
  inc=self.objective_inc if structural else self.raw_inc
  if 2*len(values)*(max(inc,default=0)+weight*max(values,default=0))+max(self.initial,default=0)>=2**120:raise ValueError('cost envelope exceeded')
  backend=self.backends[int(structural)];backend.prepare(dict(enumerate(values)),weight)
  self.structural=structural;self.prices=values;self.weight=weight;self.prepared=True
 def search(self,source,sinks):
  if self.closed or not self.prepared:raise RuntimeError('closed or unprepared search')
  targets=set(sinks);costs,parents,found=self.backends[int(self.structural)].search(source,targets)
  raw={};copied={};objectives={}
  for target in sorted(found&targets):
   u=target;seen={u};delay=self.initial[source];static=priced=0
   while u!=source:
    prev,slot=parents[u]
    if not self.fields['row_offsets'][prev]<=slot<self.fields['row_offsets'][prev+1] or self.fields['dest_ranks'][slot]!=u:raise RuntimeError('invalid path arc')
    copied[u]=(prev,slot);delay+=self.raw_inc[slot];static+=self.base[u] if self.structural else 0;priced+=self.prices[u]
    u=prev
    if u in seen:raise RuntimeError('path cycle')
    seen.add(u)
   if delay+static!=costs[target]:raise RuntimeError('raw/objective mismatch')
   raw[target]=delay;objectives[target]=delay+static+self.weight*priced
  self.last_objectives=objectives
  return raw,copied,found&targets
 def close(self):
  for backend in getattr(self,'backends',[]):backend.close()
  self.closed=True
 def __del__(self):self.close()
