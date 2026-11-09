"""Serial prepared-bound consumer with one authenticated copy per visited sink."""
import ctypes
from native_integer_rc_sink_bound import NativeIntegerRCSinkBound
from native_integer_rc_search import NativeIntegerRC

class NativeIntegerRCPreparedSinkBound(NativeIntegerRCSinkBound):
 def __init__(self,rc,bounds):
  super().__init__(rc)
  if bounds.nodes!=self.n:raise ValueError('bound graph dimension mismatch')
  self.bounds=bounds;self.bound_arrays={}
 def query(self,source,sink,budget,max_labels=10000):
  self.rc.node(source);self.rc.node(sink)
  if sink not in self.bound_arrays:
   values=self.bounds.get(sink)
   if len(values)!=self.n or values[sink]!=0 or not values.readonly:raise ValueError('immutable authenticated bound required')
   self.bound_arrays[sink]=(ctypes.c_uint64*self.n).from_buffer_copy(values)
  self.remaining_pointer=self.bound_arrays[sink]
  return NativeIntegerRC.query(self,source,sink,budget,max_labels)
 def query_bound(self,*args,**kwargs):raise ValueError('use authenticated prepared query')
