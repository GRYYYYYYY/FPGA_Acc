"""Integer graph C API; 120-bit weighted costs, bounded 64-bit original RC delays."""
import ctypes as C
from array import array
class Parents:
 def __init__(self,nodes,slots):self.nodes=nodes;self.slots=slots
 def __getitem__(self,node):
  if self.nodes[node]==(1<<64)-1:raise KeyError(node)
  return self.nodes[node],self.slots[node]
class Search:
 def __init__(self,fields,rc,binary):
  self.n=len(fields['capacities']);self.rc=rc;self.fields=fields;self.lib=C.CDLL(str(binary));self.arrays=[array('Q',fields[k]) for k in ['row_offsets','dest_ranks']]+[array('Q',rc.increments),array('Q',fields['capacities'])];assert len(self.arrays[0])==self.n+1 and self.arrays[0][0]==0 and self.arrays[0][-1]==len(self.arrays[1])==len(self.arrays[2]);assert all(a<=b for a,b in zip(self.arrays[0],self.arrays[0][1:]));assert all(v<self.n for v in self.arrays[1]);self.maxinc=max(rc.increments,default=0);self.raw=array('Q',[0])*self.n;self.pn=array('Q',[0])*self.n;self.pe=array('Q',[0])*self.n;self.settled=array('B',[0])*self.n;self.parents=Parents(self.pn,self.pe);self.price=array('Q',[0])*self.n;self.weight=0;P=C.POINTER(C.c_uint64);B=C.POINTER(C.c_uint8);self.lib.rc_tree.argtypes=[C.c_uint64]*4+[P,C.c_uint64]+[P]*8+[B];self.lib.rc_tree.restype=C.c_int
 def ptr(self,arr,kind=C.c_uint64):return (kind*len(arr)).from_buffer(arr)
 def prepare(self,prices,weight):
  assert 0<=weight<(1<<64);self.weight=weight;self.price=array('Q',(prices.get(n,0) for n in range(self.n)));assert self.n*(self.maxinc+weight*max(self.price,default=0))+max(self.rc.initial(n) for n in range(self.n))<(1<<120)
 def search(self,source,sinks):
  initial=self.rc.initial(source);assert initial+self.n*self.maxinc<(1<<64)-1;targets=array('Q',sorted(set(sinks)));args=[self.n,source,initial,self.weight,self.ptr(targets),len(targets)]+[self.ptr(x) for x in self.arrays]+[self.ptr(self.price),self.ptr(self.raw),self.ptr(self.pn),self.ptr(self.pe),self.ptr(self.settled,C.c_uint8)];status=self.lib.rc_tree(*args)
  if status:raise RuntimeError(f'C++ tree search status {status}; no partial output accepted')
  return self.raw,self.parents,{s for s in sinks if self.settled[s]}
