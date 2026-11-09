"""Separate host trace backend; state is caller-owned and serial-use only."""
import ctypes
from pathlib import Path
from types import SimpleNamespace
from native_integer_rc_search import NativeIntegerRC

class NativeIntegerRCTrace(NativeIntegerRC):
 def __init__(self,rc):
  super().__init__(rc)
  self.trace_library=ctypes.CDLL(str(Path(__file__).resolve().parents[1]/'build/rc_budget_native_trace_2026-10-06/search.so'))
  function=self.trace_library.rc_query_trace
  function.restype=ctypes.c_int;function.argtypes=[*self.lib.rc_query.argtypes,ctypes.POINTER(ctypes.c_uint8)]
  self.reads=(ctypes.c_uint8*self.n)()
  self.lib=SimpleNamespace(rc_query=lambda *args:function(*args,self.reads))
 def traced_query(self,source,sink,budget,max_labels=10000):
  ctypes.memset(self.reads,0,self.n)
  result=super().query(source,sink,budget,max_labels)
  return result,frozenset(n for n in range(self.n) if self.reads[n])
