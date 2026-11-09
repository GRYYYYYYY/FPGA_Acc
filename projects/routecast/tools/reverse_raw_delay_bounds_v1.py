"""Immutable relaxed-graph capped reverse-distance lower bounds.

Cache belongs to one copied CSR/raw-increment snapshot, not mutable prices,
capacity masks, endpoint epochs or a reused NET identity. cap=budget+1 is a
lower bound sentinel, never a general-unreachability certificate.
"""
import heapq,time,hashlib,json,sys
from array import array
from pathlib import Path

class Bound:
 def __init__(self,target,cap,values,context):self.target=target;self.cap=cap;self.values=tuple(values);self.context=context
 def get(self,node,default=None):
  if type(node) is not int or not 0<=node<len(self.values):raise ValueError('bound node')
  return self.values[node]

class ReverseBounds:
 def __init__(self,offsets,dest,increments):
  start=time.perf_counter();self.offsets=tuple(offsets);self.dest=tuple(dest);self.raw=tuple(increments);self.n=len(self.offsets)-1;self.m=len(self.dest)
  if self.n<1 or len(self.raw)!=self.m or self.offsets[0]!=0 or self.offsets[-1]!=self.m or any(a>b for a,b in zip(self.offsets,self.offsets[1:])):raise ValueError('CSR')
  if any(type(v) is not int or not 0<=v<self.n for v in self.dest) or any(type(w) is not int or not 0<=w<2**128 for w in self.raw):raise ValueError('raw domain')
  self.us=array('Q',[0])*self.m;self.reverse_offsets=array('Q',[0])*(self.n+1)
  for v in self.dest:self.reverse_offsets[v+1]+=1
  for i in range(self.n):self.reverse_offsets[i+1]+=self.reverse_offsets[i]
  cursor=array('Q',self.reverse_offsets);self.reverse_order=array('Q',[0])*self.m
  for u in range(self.n):
   for e in range(self.offsets[u],self.offsets[u+1]):v=self.dest[e];self.us[e]=u;self.reverse_order[cursor[v]]=e;cursor[v]+=1
  digest=hashlib.sha256();digest.update(array('Q',self.offsets).tobytes());digest.update(array('Q',self.dest).tobytes())
  for w in self.raw:digest.update(w.to_bytes(16,'little'))
  self.context=digest.hexdigest();self.cache={};self.hits=0;self.misses=0;self.scanned_arcs=0;self.bound_seconds=0.;self.preparation_seconds=time.perf_counter()-start
 def bound(self,target,budget):
  if type(target) is not int or not 0<=target<self.n or type(budget) is not int or not 0<=budget<2**128:raise ValueError('target/budget')
  cap=budget+1;key=(target,cap)
  if key in self.cache:self.hits+=1;return self.cache[key]
  start=time.perf_counter();self.misses+=1;dist=[cap]*self.n;dist[target]=0;queue=[(0,target)]
  while queue:
   value,v=heapq.heappop(queue)
   if value!=dist[v]:continue
   for pos in range(self.reverse_offsets[v],self.reverse_offsets[v+1]):
    e=self.reverse_order[pos];u=self.us[e];candidate=value+self.raw[e];self.scanned_arcs+=1
    if candidate<dist[u]:dist[u]=candidate;heapq.heappush(queue,(candidate,u))
  b=Bound(target,cap,dist,self.context);self.cache[key]=b;self.bound_seconds+=time.perf_counter()-start;return b
 def export(self,directory):
  directory=Path(directory);directory.mkdir(exist_ok=False);rows=[]
  for (target,cap),bound in sorted(self.cache.items()):
   p=directory/f'sink_{target}_cap_{cap}.bin'
   if cap<2**64:
    with p.open('xb') as f:array('Q',bound.values).tofile(f)
    encoding='NATIVE_ENDIAN_U64'
   else:
    p=p.with_suffix('.json');p.write_text(json.dumps(bound.values)+'\n');encoding='JSON_INTEGERS'
   rows.append(dict(target=target,cap=cap,path=str(p),encoding=encoding,byteorder=sys.byteorder,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
  return dict(context_sha256=self.context,nodes=self.n,arcs=self.m,cache_hits=self.hits,cache_misses=self.misses,reverse_arcs_examined=self.scanned_arcs,preparation_seconds=self.preparation_seconds,bound_seconds=self.bound_seconds,bounds=rows)
