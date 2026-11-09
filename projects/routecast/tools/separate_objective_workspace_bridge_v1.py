"""Independent objective increments; original raw increments remain budget delay."""
import ctypes as C
from array import array
from soft_demand_cpp_bridge_v1 import Search as Base

class Search(Base):
 def __init__(self,fields,rc,binary,objective):
  super().__init__(fields,rc,binary)
  assert len(objective)==len(rc.increments) and all(0<=v<(1<<64) for v in objective)
  self.objective=array('Q',objective);P=C.POINTER(C.c_uint64);B=C.POINTER(C.c_uint8)
  self.lib.rc_tree.argtypes=[C.c_uint64]*4+[P,C.c_uint64]+[P]*9+[B]
  self.lib.rc_workspace_create.argtypes=[C.c_uint64];self.lib.rc_workspace_create.restype=C.c_void_p
  self.lib.rc_workspace_destroy.argtypes=[C.c_void_p];self.lib.rc_workspace_destroy.restype=None
  self.lib.rc_tree_workspace.argtypes=[C.c_void_p,*self.lib.rc_tree.argtypes];self.lib.rc_tree_workspace.restype=C.c_int
  self.handle=self.lib.rc_workspace_create(self.n)
  if not self.handle:raise RuntimeError('objective workspace allocation failed')
 def prepare(self,prices,weight):
  super().prepare(prices,weight)
  assert self.n*(max(self.objective,default=0)+weight*max(self.price,default=0))+max(self.rc.initial(n) for n in range(self.n))<1<<120
 def search(self,source,sinks):
  if not self.handle:raise RuntimeError('workspace closed')
  initial=self.rc.initial(source);assert initial+self.n*self.maxinc<(1<<64)-1
  targets=array('Q',sorted(set(sinks)))
  arrays=self.arrays[:3]+[self.objective]+self.arrays[3:]
  args=[self.n,source,initial,self.weight,self.ptr(targets),len(targets)]+[self.ptr(a) for a in arrays]+[self.ptr(self.price),self.ptr(self.raw),self.ptr(self.pn),self.ptr(self.pe),self.ptr(self.settled,C.c_uint8)]
  status=self.lib.rc_tree_workspace(self.handle,*args)
  if status:raise RuntimeError(f'objective workspace status {status}')
  return self.raw,self.parents,{s for s in sinks if self.settled[s]}
 def close(self):
  if getattr(self,'handle',None):self.lib.rc_workspace_destroy(self.handle);self.handle=None
 def __del__(self):self.close()
