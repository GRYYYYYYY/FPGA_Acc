"""Owned additive CSR lower bounds, target-only compact capped vectors and LRU.

Each budget view equals a fresh min(distance,budget+1) computation. Capacity,
prices, tree/epoch state are deliberately not cached. Payload ceiling excludes
transient Dijkstra, graph CSR, external live views and Python object overhead.
"""
import hashlib,heapq,time
from array import array
from collections import OrderedDict
from types import MappingProxyType
MAX_CAP=1<<128

class Packed:
 def __init__(self,values,cap):
  self.cap=cap;self.n=len(values);bits=cap.bit_length();self.width=next(w for w in (1,2,4,8,16,17) if bits<=8*w)
  code={1:'B',2:'H',4:'I',8:'Q'}.get(self.width)
  if code:
   a=array(code,values)
   if a.itemsize!=self.width:raise ValueError('unsupported native integer layout')
   self._data=a.tobytes();self._view=memoryview(self._data).cast(code)
  else:self._data=b''.join(v.to_bytes(self.width,'little') for v in values);self._view=None
  self.bytes=len(self._data)
 def get(self,node):
  if type(node) is not int or not 0<=node<self.n:raise ValueError('bound node domain')
  if self._view is not None:return self._view[node]
  start=node*self.width;return int.from_bytes(self._data[start:start+self.width],'little')

class Bound:
 def __init__(self,target,budget,packed,context):self.target=target;self.cap=budget+1;self._packed=packed;self.context=context
 def get(self,node,default=None):return min(self.cap,self._packed.get(node))

class CompactReverseBounds:
 def __init__(self,offsets,dest,increments,max_cache_bytes=2*2**30,target_budget_ceilings=None):
  start=time.perf_counter();self.offsets=tuple(offsets);self.dest=tuple(dest);self.raw=tuple(increments);self.n=len(self.offsets)-1;self.m=len(self.dest)
  if self.n<1 or len(self.raw)!=self.m or self.offsets[0]!=0 or self.offsets[-1]!=self.m or any(type(v) is not int or v<0 for v in self.offsets) or any(a>b for a,b in zip(self.offsets,self.offsets[1:])):raise ValueError('CSR domain')
  if any(type(v) is not int or not 0<=v<self.n for v in self.dest) or any(type(v) is not int or not 0<=v<MAX_CAP for v in self.raw):raise ValueError('raw cost/destination domain')
  if type(max_cache_bytes) is not int or max_cache_bytes<0:raise ValueError('payload ceiling')
  ceilings=dict(target_budget_ceilings or {})
  if any(type(n) is not int or not 0<=n<self.n or type(b) is not int or not 0<=b<MAX_CAP for n,b in ceilings.items()):raise ValueError('prepared budget domain')
  self.ceilings=MappingProxyType(ceilings);self.limit=max_cache_bytes;self.us=array('Q',[0])*self.m;self.reverse_offsets=array('Q',[0])*(self.n+1)
  for node in self.dest:self.reverse_offsets[node+1]+=1
  for node in range(self.n):self.reverse_offsets[node+1]+=self.reverse_offsets[node]
  cursor=array('Q',self.reverse_offsets);self.reverse_order=array('Q',[0])*self.m
  for u in range(self.n):
   for edge in range(self.offsets[u],self.offsets[u+1]):v=self.dest[edge];self.us[edge]=u;self.reverse_order[cursor[v]]=edge;cursor[v]+=1
  h=hashlib.sha256();h.update(array('Q',self.offsets).tobytes());h.update(array('Q',self.dest).tobytes())
  for value in self.raw:h.update(value.to_bytes(16,'little'))
  self.context=h.hexdigest();self.cache=OrderedDict();self.cached_bytes=0;self.peak_cached_bytes=0;self.hits=0;self.misses=0;self.growth_rebuilds=0;self.evictions=0;self.uncached_vectors=0;self.scanned_arcs=0;self.bound_seconds=0.;self.preparation_seconds=time.perf_counter()-start
 def _compute(self,target,cap):
  distances=[cap]*self.n;distances[target]=0;queue=[(0,target)]
  while queue:
   value,v=heapq.heappop(queue)
   if value!=distances[v]:continue
   for pos in range(self.reverse_offsets[v],self.reverse_offsets[v+1]):
    edge=self.reverse_order[pos];u=self.us[edge];candidate=value+self.raw[edge];self.scanned_arcs+=1
    if candidate<distances[u]:distances[u]=candidate;heapq.heappush(queue,(candidate,u))
  return Packed(distances,cap)
 def bound(self,target,budget):
  if type(target) is not int or not 0<=target<self.n or type(budget) is not int or not 0<=budget<MAX_CAP:raise ValueError('target/budget domain')
  requested=budget+1;prior=self.cache.get(target)
  if prior is not None and prior.cap>=requested:
   self.hits+=1;self.cache.move_to_end(target);return Bound(target,budget,prior,self.context)
  self.misses+=1;start=time.perf_counter();cap=max(requested,self.ceilings.get(target,-1)+1)
  if prior is not None:self.growth_rebuilds+=1;cap=max(cap,min(MAX_CAP,prior.cap*2))
  packed=self._compute(target,cap);self.bound_seconds+=time.perf_counter()-start
  if packed.bytes<=self.limit:
   if prior is not None:self.cached_bytes-=self.cache.pop(target).bytes
   while self.cache and self.cached_bytes+packed.bytes>self.limit:
    key,old=self.cache.popitem(last=False);self.cached_bytes-=old.bytes;self.evictions+=1
   self.cache[target]=packed;self.cached_bytes+=packed.bytes;self.peak_cached_bytes=max(self.peak_cached_bytes,self.cached_bytes)
  else:self.uncached_vectors+=1
  assert self.cached_bytes<=self.limit
  return Bound(target,budget,packed,self.context)
 def stats(self):return dict(nodes=self.n,arcs=self.m,cached_targets=len(self.cache),cached_payload_bytes=self.cached_bytes,peak_cached_payload_bytes=self.peak_cached_bytes,payload_limit_bytes=self.limit,hits=self.hits,misses=self.misses,growth_rebuilds=self.growth_rebuilds,evictions=self.evictions,uncached_vectors=self.uncached_vectors,scanned_arcs=self.scanned_arcs,preparation_seconds=self.preparation_seconds,bound_seconds=self.bound_seconds,context_sha256=self.context,scope='Retained packed payload only. No prediction state or mutable search contexts cached.')
