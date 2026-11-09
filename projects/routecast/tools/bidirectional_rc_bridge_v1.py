"""Owned C++ graph/workspace for single-target search, exact original slots."""
import ctypes as C
from array import array

class Bidirectional:
    def __init__(self,fields,rc,binary):
        self.fields,self.rc = fields,rc
        self.n = len(fields['capacities'])
        self.maxinc = max(rc.increments,default=0)
        self.arrays = [array('Q',fields[k]) for k in ['row_offsets','dest_ranks']]+[array('Q',rc.increments),array('Q',fields['capacities'])]
        assert len(self.arrays[0])==self.n+1 and self.arrays[0][0]==0
        assert self.arrays[0][-1]==len(self.arrays[1])==len(self.arrays[2])
        assert all(a<=b for a,b in zip(self.arrays[0],self.arrays[0][1:]))
        assert all(v<self.n for v in self.arrays[1])
        self.lib = C.CDLL(str(binary));P = C.POINTER(C.c_uint64)
        self.lib.rc_bidi_create.argtypes=[C.c_uint64]+[P]*4
        self.lib.rc_bidi_create.restype=C.c_void_p
        self.lib.rc_bidi_destroy.argtypes=[C.c_void_p]
        self.lib.rc_bidi_destroy.restype=None
        self.lib.rc_bidi_search.argtypes=[C.c_void_p]+[C.c_uint64]*4+[P,P,C.c_uint64]+[P]*5
        self.lib.rc_bidi_search.restype=C.c_int
        self.handle = self.lib.rc_bidi_create(self.n,*[self.ptr(a) for a in self.arrays])
        if not self.handle:raise RuntimeError('bidirectional graph validation/allocation failed')
        self.slots=array('Q',[0])*self.n
        self.prepare({},0)
    @staticmethod
    def ptr(a):return (C.c_uint64*len(a)).from_buffer(a)
    def prepare(self,prices,weight):
        assert 0<=weight<2**64
        price=array('Q',(prices.get(u,0) for u in range(self.n)))
        assert 2*self.n*(self.maxinc+weight*max(price,default=0))+max(self.rc.initial(u) for u in range(self.n))<2**120
        self.price,self.weight = price,weight
    def search(self,source,sink):
        assert 0<=source<self.n and 0<=sink<self.n
        assert self.fields['capacities'][source] and self.fields['capacities'][sink]
        initial=self.rc.initial(source)
        assert initial+self.n*self.maxinc<2**64-1
        count,raw,low,high=[C.c_uint64() for _ in range(4)]
        stats=(C.c_uint64*4)()
        status=self.lib.rc_bidi_search(self.handle,source,sink,initial,self.weight,self.ptr(self.price),self.ptr(self.slots),self.n,C.byref(count),C.byref(raw),C.byref(low),C.byref(high),stats)
        if status==1:return None
        if status:raise RuntimeError(f'bidirectional query status {status}; output rejected')
        return dict(slots=list(self.slots[:count.value]),raw=raw.value,objective=low.value+(high.value<<64),scanned_arcs=list(stats[:2]),settled_nodes=list(stats[2:]))
    def close(self):
        if getattr(self,'handle',None):self.lib.rc_bidi_destroy(self.handle);self.handle=None
    def __del__(self):self.close()
