"""Standalone numeric experiment; not imported by frozen full-model batch."""
import ctypes as C
from pathlib import Path
R=Path(__file__).resolve().parents[1];BINARY=R/'build/map_priority_materialize_v2_2026-10-20/materialize.so'
def materialize(endpoints,allowed,terminal,bits,scale,denominator):
 n=len(allowed)
 if not n or len(terminal)!=n or len(endpoints)!=8*n or any(type(v) not in [bool,int] or v not in [0,1] for v in [*allowed,*terminal]):raise ValueError('materializer array domains')
 if len(bits)!=8 or type(scale) is not int or type(denominator) is not int or not 0<scale<2**64 or not 0<denominator<2**64:raise ValueError('materializer integer domains')
 lib=C.CDLL(str(BINARY));lib.rc_map_materialize.argtypes=[C.c_uint64,C.POINTER(C.c_float),C.POINTER(C.c_ubyte),C.POINTER(C.c_ubyte),C.c_uint32,C.c_uint64,C.c_uint64,C.POINTER(C.c_uint64)];lib.rc_map_materialize.restype=C.c_int
 source=(C.c_float*(n*2)).from_buffer_copy(endpoints);mask=(C.c_ubyte*n)(*allowed);term=(C.c_ubyte*n)(*terminal);words=(C.c_uint64*(n*2))();status=lib.rc_map_materialize(n,source,mask,term,int(bits,16),scale,denominator,words)
 if status:raise ValueError('materializer rejected '+str(status))
 return tuple(words[2*i]+(words[2*i+1]<<64) for i in range(n))
