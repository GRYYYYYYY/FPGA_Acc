"""Independent sink-bound policy; caller authenticates exact remaining delays."""
import ctypes
from array import array
from pathlib import Path
from types import SimpleNamespace
from native_integer_rc_delta_search import NativeIntegerRCDeltaSearch

class NativeIntegerRCSinkBound(NativeIntegerRCDeltaSearch):
 def __init__(self,rc):
  super().__init__(rc);self.bound_library=ctypes.CDLL(str(Path(__file__).resolve().parents[1]/'build/rc_budget_native_sink_bound_2026-10-06/search.so'));function=self.bound_library.rc_query_sink_bound
  function.restype=ctypes.c_int;function.argtypes=[*self.lib.rc_query.argtypes,ctypes.POINTER(ctypes.c_uint64)]
  self.lib=SimpleNamespace(rc_query=lambda *args:function(*args,self.remaining_pointer))
 def query(self,*args,**kwargs):raise ValueError('authenticated sink bound required: use query_bound')
 def query_bound(self,source,sink,budget,remaining,max_labels=10000):
  self.rc.node(source);self.rc.node(sink)
  staged=array('Q',[(1<<64)-1])*self.n
  for node,value in remaining.items():
   if type(node) is not int or not 0<=node<self.n or type(value) is not int or not 0<=value<(1<<64)-1:raise ValueError('uint64 finite remaining bound required')
   staged[node]=value
  if staged[sink]!=0:raise ValueError('sink remaining delay must be zero')
  self.remaining=staged;self.remaining_pointer=(ctypes.c_uint64*self.n).from_buffer(staged)
  return super().query(source,sink,budget,max_labels)
