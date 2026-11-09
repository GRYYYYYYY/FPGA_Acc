"""Diagnostic operation counts; timings include instrumentation overhead."""
import ctypes as C
from soft_demand_workspace_bridge_v1 import Search as Base
class Search(Base):
 def __init__(self,*args):
  super().__init__(*args)
  self.lib.rc_workspace_stats.argtypes=[C.c_void_p,C.POINTER(C.c_uint64)]
  self.lib.rc_workspace_stats.restype=C.c_int
  self.metrics=[]
 def search(self,source,sinks):
  result=super().search(source,sinks)
  values=(C.c_uint64*8)()
  if self.lib.rc_workspace_stats(self.handle,values):raise RuntimeError('stats retrieval failed')
  self.metrics.append(dict(source=source,targets=len(set(sinks)),settled=values[0],scanned_arcs=values[1],pushes=values[2],pops=values[3],stale=values[4],relaxations=values[5],touched=values[6],reset_nodes=values[7]))
  return result
