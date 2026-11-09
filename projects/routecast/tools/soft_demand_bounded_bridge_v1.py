import ctypes as C
from soft_demand_workspace_bridge_v1 import Search as Base
class Search(Base):
 def __init__(self,*args):
  self.limit=None;super().__init__(*args)
  self.lib.rc_tree_workspace_bounded.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,*self.lib.rc_tree_workspace.argtypes[1:]];self.lib.rc_tree_workspace_bounded.restype=C.c_int
 def _run(self,*args):
  if not self.handle:raise RuntimeError('workspace closed')
  if self.limit is None:return self.lib.rc_tree_workspace(self.handle,*args)
  return self.lib.rc_tree_workspace_bounded(self.handle,self.limit>>64,self.limit&((1<<64)-1),*args)
 def search(self,source,sinks,upper_bound=None):
  if upper_bound is not None and (type(upper_bound) is not int or not 0<=upper_bound<(1<<120)):raise ValueError('invalid certified bound')
  self.limit=upper_bound
  try:return super().search(source,sinks)
  finally:self.limit=None
