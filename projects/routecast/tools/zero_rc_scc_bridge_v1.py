"""Exact directed zero-increment SCC partition, no path-lift assumption."""
import ctypes as C
from array import array
def partition(fields,increments,binary):
 n=len(fields['capacities']);arrays=[array('Q',fields[k]) for k in ['row_offsets','dest_ranks']]+[array('Q',increments),array('Q',fields['capacities'])]
 assert len(arrays[0])==n+1 and arrays[0][-1]==len(arrays[1])==len(arrays[2])
 result=array('Q',[0])*n;P=C.POINTER(C.c_uint64);library=C.CDLL(str(binary))
 library.zero_rc_scc.argtypes=[C.c_uint64]+[P]*6;library.zero_rc_scc.restype=C.c_int
 pointers=[(C.c_uint64*len(a)).from_buffer(a) for a in [*arrays,result]];count=C.c_uint64()
 status=library.zero_rc_scc(n,*pointers,C.byref(count))
 if status:raise RuntimeError(f'zero RC SCC status {status}')
 return result,count.value
