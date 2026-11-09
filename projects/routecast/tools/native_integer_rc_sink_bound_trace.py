"""Serial prepared sink-bound search with sparse positive-cost read tracing."""
import ctypes
from pathlib import Path
from types import SimpleNamespace
from native_integer_rc_prepared_sink_bound import NativeIntegerRCPreparedSinkBound

class NativeIntegerRCSinkBoundTrace(NativeIntegerRCPreparedSinkBound):
 def __init__(self,rc,bounds):
  super().__init__(rc,bounds)
  self.trace_library=ctypes.CDLL(str(Path(__file__).resolve().parents[1]/'build/rc_budget_native_sink_bound_trace_2026-10-06/search.so'));function=self.trace_library.rc_query_sink_bound_trace
  function.restype=ctypes.c_int;function.argtypes=[*self.bound_library.rc_query_sink_bound.argtypes,ctypes.POINTER(ctypes.c_uint8),ctypes.POINTER(ctypes.c_uint64),ctypes.POINTER(ctypes.c_uint64)]
  self.reads=(ctypes.c_uint8*self.n)();self.touched=(ctypes.c_uint64*self.n)();self.count=ctypes.c_uint64(0);self.previous_reads=frozenset()
  self.lib=SimpleNamespace(rc_query=lambda *args:function(*args,self.remaining_pointer,self.reads,self.touched,ctypes.byref(self.count)))
 def traced_query(self,source,sink,budget,max_labels=10000):
  for node in self.previous_reads:self.reads[node]=0
  self.count.value=0
  try:result=super().query(source,sink,budget,max_labels)
  finally:self.previous_reads=frozenset(self.touched[:self.count.value])
  return result,self.previous_reads
 def query(self,source,sink,budget,max_labels=10000):return self.traced_query(source,sink,budget,max_labels)[0]
