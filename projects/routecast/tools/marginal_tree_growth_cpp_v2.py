"""Sparse-reset C++ branch search; serial owned workspace over immutable CSR."""
import ctypes as C
from array import array

class Growth:
 def __init__(self,fields,increments,binary):
  self.f=fields;self.n=len(fields['capacities']);self.inc=increments;self.maxinc=max(increments,default=0)
  self.arrays=[array('Q',fields[k]) for k in ['row_offsets','dest_ranks']]+[array('Q',increments),array('Q',fields['capacities'])]
  assert len(self.arrays[0])==self.n+1 and self.arrays[0][-1]==len(self.arrays[1])==len(increments)==len(fields['edge_ids'])
  assert self.arrays[0][0]==0 and all(a<=b for a,b in zip(self.arrays[0],self.arrays[0][1:]))
  assert all(v<self.n for v in self.arrays[1])
  self.lib=C.CDLL(str(binary));P=C.POINTER(C.c_uint64);B=C.POINTER(C.c_uint8)
  self.lib.marginal_create.argtypes=[C.c_uint64];self.lib.marginal_create.restype=C.c_void_p
  self.lib.marginal_destroy.argtypes=[C.c_void_p];self.lib.marginal_destroy.restype=None
  self.lib.marginal_branch.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_uint64]+[P]*7+[B]+[P]*6
  self.lib.marginal_branch.restype=C.c_int
  self.handle=self.lib.marginal_create(self.n)
  if not self.handle:raise RuntimeError('growth workspace allocation failed')
  self.owned=array('B',[0])*self.n;self.output=array('Q',[0])*self.n
  self.last_owned=set();self.price=array('Q',[0])*self.n;self.weight=0
 def ptr(self,a,kind=C.c_uint64):return (kind*len(a)).from_buffer(a)
 def prepare(self,prices,weight):
  assert 0<=weight<1<<64
  self.price=array('Q',(prices.get(n,0) for n in range(self.n)));self.weight=weight
  assert self.n*(self.maxinc+weight*max(self.price,default=0))<1<<120
 def grow(self,source,sinks,initial,budgets):
  if not self.handle:raise RuntimeError('growth workspace closed')
  assert 0<=source<self.n and 0<=initial<(1<<64)-1 and all(0<=s<self.n for s in sinks)
  assert initial+self.n*self.maxinc<(1<<64)-1
  for n in self.last_owned:self.owned[n]=0
  owned={source};self.last_owned=owned;self.owned[source]=1
  paths={source:()};raw={source:initial};parents={};records=[];branches=[]
  for sink in sinks:
   if sink not in owned:
    seeds=array('Q',sorted(owned));prefix=array('Q',(raw[n] for n in seeds))
    outputs=[C.c_uint64() for _ in range(5)]
    status=self.lib.marginal_branch(self.handle,sink,self.weight,len(seeds),self.ptr(seeds),self.ptr(prefix),*[self.ptr(a) for a in self.arrays],self.ptr(self.price),self.ptr(self.owned,C.c_uint8),self.ptr(self.output),*[C.byref(x) for x in outputs])
    if status==1:return dict(status='RETAIN_OLD_TREE_UNREACHABLE',failed_sink=sink)
    if status:raise RuntimeError(f'marginal branch error {status}')
    count,attachment,delay,low,high=[x.value for x in outputs]
    if delay>budgets[sink]:return dict(status='RETAIN_OLD_TREE_BUDGET',failed_sink=sink,delay=delay,budget=budgets[sink])
    u=attachment;new_edges=[]
    for slot in self.output[:count]:
     v=self.f['dest_ranks'][slot];eid=self.f['edge_ids'][slot]
     assert self.f['row_offsets'][u]<=slot<self.f['row_offsets'][u+1] and v not in owned
     parents[v]=(u,eid);raw[v]=raw[u]+self.inc[slot];paths[v]=paths[u]+(eid,)
     owned.add(v);self.owned[v]=1;u=v;new_edges.append(eid)
    assert u==sink and raw[sink]==delay
    branches.append(dict(sink=sink,attachment=attachment,incremental_cost=low+(high<<64),new_edges=new_edges))
   if raw[sink]>budgets[sink]:return dict(status='RETAIN_OLD_TREE_BUDGET',failed_sink=sink,delay=raw[sink],budget=budgets[sink])
   records.append(dict(sink=sink,edges=list(paths[sink]),delay=raw[sink]))
  return dict(status='CANDIDATE',records=records,branches=branches,parent=parents,raw=raw,owned=sorted(owned))
 def close(self):
  if getattr(self,'handle',None):self.lib.marginal_destroy(self.handle);self.handle=None
 def __del__(self):self.close()
