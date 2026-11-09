"""Batched reverse single-SINK search with original forward edge costs."""
import ctypes as C
from array import array
from types import SimpleNamespace
from soft_demand_cpp_bridge_v1 import Search as Base
class Reverse(Base):
 def __init__(self,fields,rc,binary):
  n=len(fields['capacities']);incoming=[[] for _ in range(n)]
  for u in range(n):
   for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
    incoming[fields['dest_ranks'][slot]].append((u,slot))
  rev={k:array('Q') for k in ['row_offsets','dest_ranks','capacities']}
  rev['capacities'].extend(fields['capacities']);rev['row_offsets'].append(0)
  increments=[];self.original_slots=[]
  for arcs in incoming:
   for u,slot in arcs:rev['dest_ranks'].append(u);increments.append(rc.increments[slot]);self.original_slots.append(slot)
   rev['row_offsets'].append(len(increments))
  super().__init__(rev,SimpleNamespace(increments=increments,initial=lambda node:0),binary)
  self.original=fields;self.original_rc=rc
  self.lib.rc_workspace_create.argtypes=[C.c_uint64];self.lib.rc_workspace_create.restype=C.c_void_p
  self.lib.rc_workspace_destroy.argtypes=[C.c_void_p];self.lib.rc_workspace_destroy.restype=None
  self.lib.rc_reverse_workspace.argtypes=[C.c_void_p,*self.lib.rc_tree.argtypes];self.lib.rc_reverse_workspace.restype=C.c_int
  self.lib.rc_reverse_cost.argtypes=[C.c_void_p,C.c_uint64,C.POINTER(C.c_uint64),C.POINTER(C.c_uint64)];self.lib.rc_reverse_cost.restype=C.c_int
  self.handle=self.lib.rc_workspace_create(self.n)
  if not self.handle:raise RuntimeError('reverse workspace allocation failed')
  self.lib.rc_tree=self._run
 def _run(self,*args):return self.lib.rc_reverse_workspace(self.handle,*args)
 def batch(self,sink,sources):
  sources=set(sources);_,_,settled=super().search(sink,sources);answers={}
  for source in sorted(sources):
   if source not in settled:answers[source]=None;continue
   u=source;path=[];seen={u}
   while u!=sink:
    v,revslot=self.parents[u];slot=self.original_slots[revslot]
    assert self.original['dest_ranks'][slot]==v
    assert self.original['row_offsets'][u]<=slot<self.original['row_offsets'][u+1]
    path.append(slot);u=v;assert u not in seen;seen.add(u)
   low=C.c_uint64();high=C.c_uint64()
   assert self.lib.rc_reverse_cost(self.handle,source,C.byref(low),C.byref(high))==0
   initial=self.original_rc.initial(source)
   answers[source]=dict(slots=path,raw=initial+self.raw[source],objective=initial+low.value+(high.value<<64))
  return answers
 def close(self):
  if getattr(self,'handle',None):self.lib.rc_workspace_destroy(self.handle);self.handle=None
 def __del__(self):self.close()
