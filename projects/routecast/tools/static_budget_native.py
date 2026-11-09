"""Private immutable graph plus exact128bit fixed-cap reachability query."""
import ctypes
from array import array
from pathlib import Path
class StaticBudgetNative:
 def __init__(self,rows,dest,inc,caps,binary=None):
  Q=ctypes.c_uint64;P=ctypes.POINTER(Q);V=ctypes.c_void_p;self.lib=ctypes.CDLL(str(binary or Path(__file__).resolve().parents[1]/'build/static_budget_native_2026-10-07/search.so'));self.lib.floor_create.argtypes=[Q,Q,P,P,P,P,ctypes.POINTER(V)];self.lib.floor_create.restype=ctypes.c_int;self.lib.floor_query.argtypes=[V,*([Q]*6),*([P]*5)];self.lib.floor_query.restype=ctypes.c_int;self.lib.floor_destroy.argtypes=[V];self.lib.floor_destroy.restype=None
  self.n=len(caps)
  if len(rows)!=self.n+1 or len(dest)!=len(inc):raise ValueError('invalid dimensions')
  buffers=[];ptrs=[]
  for values in [rows,dest,inc,caps]:
   if any(type(v) is not int or not 0<=v<2**64 for v in values):raise ValueError('uint64 graph transport')
   a=array('Q',values);buffers.append(a);ptrs.append((Q*len(a)).from_buffer(a))
  self.handle=V();code=self.lib.floor_create(self.n,len(dest),*ptrs,ctypes.byref(self.handle))
  if code:raise ValueError(f'graph create {code}')
 def query(self,source,initial,budget,targets):
  targets=sorted(set(targets))
  if type(source) is not int or not 0<=source<self.n or any(type(v) is not int or not 0<=v<2**128 for v in [initial,budget]) or any(type(v) is not int or not 0<=v<self.n for v in targets):raise ValueError('invalid query')
  if not self.handle.value:raise ValueError('closed graph')
  Q=ctypes.c_uint64;t=(Q*len(targets))(*targets);lo=(Q*len(targets))();hi=(Q*len(targets))();flags=(Q*len(targets))();stats=(Q*2)();mask=2**64-1;code=self.lib.floor_query(self.handle,source,initial&mask,initial>>64,budget&mask,budget>>64,len(targets),t,lo,hi,flags,stats)
  if code:raise ValueError(f'query {code}')
  return dict(target_minima={n:(lo[k]|(hi[k]<<64)) if flags[k] else None for k,n in enumerate(targets)},settled_nodes=stats[0],examined_edges=stats[1],all_targets_settled=all(flags))
 def close(self):
  if self.handle.value:self.lib.floor_destroy(self.handle);self.handle=ctypes.c_void_p()
