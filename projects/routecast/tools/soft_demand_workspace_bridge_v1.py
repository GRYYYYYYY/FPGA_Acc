"""Serial owned C++ workspace; same all-node observable search arrays as original."""
import ctypes as C
from soft_demand_cpp_bridge_v1 import Search as Base
class Search(Base):
 def __init__(self,fields,rc,binary):
  super().__init__(fields,rc,binary)
  self.lib.rc_workspace_create.argtypes=[C.c_uint64];self.lib.rc_workspace_create.restype=C.c_void_p
  self.lib.rc_workspace_destroy.argtypes=[C.c_void_p];self.lib.rc_workspace_destroy.restype=None
  self.lib.rc_tree_workspace.argtypes=[C.c_void_p,*self.lib.rc_tree.argtypes];self.lib.rc_tree_workspace.restype=C.c_int
  self.handle=self.lib.rc_workspace_create(self.n)
  if not self.handle:raise RuntimeError('workspace allocation failed')
  self.lib.rc_tree=self._run
 def _run(self,*args):
  if not self.handle:raise RuntimeError('workspace closed')
  return self.lib.rc_tree_workspace(self.handle,*args)
 def close(self):
  if getattr(self,'handle',None):self.lib.rc_workspace_destroy(self.handle);self.handle=None
 def __del__(self):
  self.close()
