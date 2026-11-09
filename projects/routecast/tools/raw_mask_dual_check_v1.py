"""Independent exhaustive-edge feasible-potential/cut certificate checker ABI."""
import ctypes as C
from array import array
U=C.c_uint64;I=C.c_uint32;B=C.c_uint8
class Checker:
 def __init__(self,binary):
  self.lib=C.CDLL(str(binary));self.fn=self.lib.verify_raw_mask_dual
  self.fn.argtypes=[U,U,C.POINTER(I),C.POINTER(I),C.POINTER(U),C.POINTER(I),C.POINTER(U),C.POINTER(B),C.POINTER(B),U,U,U,C.c_int,C.POINTER(U),C.POINTER(U)];self.fn.restype=C.c_int
 def check(self,us,vs,weights,caps,potentials,cut,blocked,source,initial,cutoff,require_cut):
  n=len(caps);m=len(us)
  if any(len(a)!=m for a in [vs,weights]) or any(len(a)!=n for a in [potentials,cut,blocked]):raise ValueError('certificate dimensions')
  if any(a.typecode!='I' or a.itemsize!=4 for a in [us,vs,caps]) or any(a.typecode!='Q' or a.itemsize!=8 for a in [weights,potentials]):raise ValueError('certificate ABI')
  if any(type(x) is not int or not 0<=x<2**64 for x in [source,initial,cutoff]):raise ValueError('scalar domain')
  def ptr(a,t):return (t*len(a)).from_buffer(a)
  bad=U();checked=U();status=self.fn(n,m,ptr(us,I),ptr(vs,I),ptr(weights,U),ptr(caps,I),ptr(potentials,U),ptr(cut,B),ptr(blocked,B),source,initial,cutoff,int(bool(require_cut)),C.byref(bad),C.byref(checked))
  if status:raise ValueError(f'dual/cut certificate rejected status={status} index={bad.value}')
  return checked.value
