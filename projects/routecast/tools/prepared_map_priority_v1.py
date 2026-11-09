"""Owned immutable-by-contract C priority/mask buffers; built once per expansion."""
import ctypes as C
from pathlib import Path
from types import SimpleNamespace
from wide_cost_search_bridge_v2 import Word
R=Path(__file__).resolve().parents[1];BINARY=R/'build/map_priority_materialize_v3_2026-10-20/materialize.so'
class Priority:
 def __init__(self,allowed):
  self.n=len(allowed)
  if not self.n or any(type(v) not in [int,bool] or v not in [0,1] for v in allowed):raise ValueError('priority mask')
  self.allowed=tuple(allowed);self.mask=(C.c_ubyte*self.n)(*allowed);self.storage=(C.c_uint64*(2*self.n))();self.words=SimpleNamespace(buffer=C.cast(self.storage,C.POINTER(Word)));self.maximum=0
 @classmethod
 def materialize(cls,endpoints,allowed,terminal,bits,scale,denominator):
  obj=cls(allowed);n=obj.n
  if len(terminal)!=n or any(type(x) not in [int,bool] or x not in [0,1] for x in terminal) or len(endpoints)!=n*8:raise ValueError('priority arrays')
  if len(bits)!=8 or type(scale) is not int or type(denominator) is not int or not 0<scale<2**64 or not 0<denominator<2**64:raise ValueError('priority integers')
  lib=C.CDLL(str(BINARY));lib.rc_map_materialize.argtypes=[C.c_uint64,C.POINTER(C.c_float),C.POINTER(C.c_ubyte),C.POINTER(C.c_ubyte),C.c_uint32,C.c_uint64,C.c_uint64,C.POINTER(C.c_uint64),C.POINTER(C.c_uint64)];lib.rc_map_materialize.restype=C.c_int;src=(C.c_float*(2*n)).from_buffer_copy(endpoints);term=(C.c_ubyte*n)(*terminal);maximum=(C.c_uint64*2)();rc=lib.rc_map_materialize(n,src,obj.mask,term,int(bits,16),scale,denominator,obj.storage,maximum)
  if rc:raise ValueError('priority kernel rejected '+str(rc))
  obj.maximum=maximum[0]+(maximum[1]<<64);return obj
