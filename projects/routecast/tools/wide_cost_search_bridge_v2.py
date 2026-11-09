"""Two-limb cost ABI with checked <2**120 envelopes and legacy search order.

IDs, capacities, slots, counters remain u64. Python validates every cost before
conversion, so no ctypes truncation is used as a numerical policy.
"""
import ctypes as C
from array import array
from soft_demand_cpp_bridge_v1 import Parents

LIMIT = 1 << 120
NONE = (1 << 128) - 1
MASK = (1 << 64) - 1

class Word(C.Structure):
    _fields_ = [('lo', C.c_uint64), ('hi', C.c_uint64)]

    @classmethod
    def of(cls, value):
        if type(value) is not int or not 0 <= value < 1 << 128:
            raise ValueError('invalid unsigned 128-bit cost')
        return cls(value & MASK, value >> 64)

    def integer(self):return self.lo | (self.hi << 64)

assert C.sizeof(Word) == 16 and C.alignment(Word) == 8
P = C.POINTER(C.c_uint64)
W = C.POINTER(Word)
B = C.POINTER(C.c_uint8)

class Words:
    def __init__(self, values):
        values = tuple(values)
        self.buffer = (Word * len(values))()
        for i, value in enumerate(values):self[i] = value
    def __len__(self):return len(self.buffer)
    def __getitem__(self, index):
        if isinstance(index, slice):return [x.integer() for x in self.buffer[index]]
        return self.buffer[index].integer()
    def __setitem__(self, index, value):
        if type(value) is not int or not 0 <= value < 1 << 128:
            raise ValueError('invalid unsigned 128-bit cost')
        # Assign only POD members. Whole-structure ctypes assignment retains
        # one _objects entry per index, although this ABI contains no pointers.
        word = self.buffer[index]
        word.lo = value & MASK
        word.hi = value >> 64

def ptr(a, kind=C.c_uint64):return (kind * len(a)).from_buffer(a)

class Domain:
    def __init__(self, fields, rc, binary):
        self.closed = False
        self.fields, self.rc = fields, rc
        self.n = len(fields['capacities'])
        self.row = array('Q', fields['row_offsets'])
        self.dest = array('Q', fields['dest_ranks'])
        self.cap = array('Q', fields['capacities'])
        self.inc = Words(rc.increments)
        self.initial = tuple(rc.initial(u) for u in range(self.n))
        if (not self.n or len(self.row) != self.n + 1 or self.row[0] or
            self.row[-1] != len(self.dest) or len(self.dest) != len(self.inc) or
            any(a > b for a,b in zip(self.row,self.row[1:])) or any(v >= self.n for v in self.dest)):
            raise ValueError('graph domain mismatch')
        if any(type(v) is not int or not 0 <= v < LIMIT for v in self.initial):
            raise ValueError('initial cost domain')
        self.maxinc, self.maxinitial = max(rc.increments, default=0), max(self.initial)
        self.lib = C.CDLL(str(binary))
        self.price = Words([0] * self.n)
        self.weight = 0
        self.prepared = False

    def prepare(self, prices, weight):
        if self.closed:raise RuntimeError('closed search')
        values = tuple(prices.get(u, 0) for u in range(self.n))
        if type(weight) is not int or not 0 <= weight < LIMIT or any(type(v) is not int or not 0 <= v < LIMIT for v in values):
            raise ValueError('invalid prices or weight')
        if 2*self.n*(self.maxinc+weight*max(values,default=0))+self.maxinitial >= LIMIT:
            raise ValueError('cost envelope exceeded')
        self.price, self.weight = Words(values), weight
        self.prepared = True

    def check(self, source, targets):
        if self.closed or not self.prepared:raise RuntimeError('closed or unprepared search')
        if any(type(u) is not int or not 0 <= u < self.n for u in [source,*targets]):
            raise ValueError('query node domain')

class Forward(Domain):
    def __init__(self, fields, rc, binary):
        super().__init__(fields, rc, binary)
        self.raw = Words([0] * self.n)
        self.pn, self.pe = array('Q', [0])*self.n, array('Q', [0])*self.n
        self.settled = array('B', [0])*self.n
        self.parents = Parents(self.pn,self.pe)
        self.lib.rc_workspace_create.argtypes = [C.c_uint64]
        self.lib.rc_workspace_create.restype = C.c_void_p
        self.lib.rc_workspace_destroy.argtypes = [C.c_void_p]
        self.lib.rc_workspace_destroy.restype = None
        self.lib.rc_tree_workspace.argtypes = [C.c_void_p,C.c_uint64,C.c_uint64,W,W,P,C.c_uint64,P,P,W,P,W,W,P,P,B]
        self.lib.rc_tree_workspace.restype = C.c_int
        self.handle = self.lib.rc_workspace_create(self.n)
        if not self.handle:raise RuntimeError('wide workspace allocation failed')

    def search(self, source, sinks):
        targets = set(sinks);self.check(source,targets)
        ts = array('Q',sorted(targets))
        initial,weight = Word.of(self.initial[source]),Word.of(self.weight)
        status = self.lib.rc_tree_workspace(self.handle,self.n,source,C.byref(initial),C.byref(weight),ptr(ts),len(ts),ptr(self.row),ptr(self.dest),self.inc.buffer,ptr(self.cap),self.price.buffer,self.raw.buffer,ptr(self.pn),ptr(self.pe),ptr(self.settled,C.c_uint8))
        if status:raise RuntimeError(f'wide forward status {status}; output rejected')
        return self.raw,self.parents,{s for s in targets if self.settled[s]}

    def close(self):
        if getattr(self,'handle',None):self.lib.rc_workspace_destroy(self.handle);self.handle=None
        self.closed=True
    def __del__(self):self.close()

class Bidirectional(Domain):
    def __init__(self, fields, rc, binary):
        super().__init__(fields,rc,binary)
        self.lib.rc_bidi_create.argtypes = [C.c_uint64,P,P,W,P]
        self.lib.rc_bidi_create.restype = C.c_void_p
        self.lib.rc_bidi_destroy.argtypes = [C.c_void_p]
        self.lib.rc_bidi_destroy.restype = None
        self.lib.rc_bidi_search.argtypes = [C.c_void_p,C.c_uint64,C.c_uint64,W,W,W,P,C.c_uint64,P,W,P,P,P]
        self.lib.rc_bidi_search.restype = C.c_int
        self.handle = self.lib.rc_bidi_create(self.n,ptr(self.row),ptr(self.dest),self.inc.buffer,ptr(self.cap))
        if not self.handle:raise RuntimeError('wide bidirectional graph allocation failed')
        self.slots = array('Q',[0])*self.n

    def search(self, source, sink):
        self.check(source,[sink])
        if not self.cap[source] or not self.cap[sink]:raise ValueError('disabled endpoint')
        initial,weight = Word.of(self.initial[source]),Word.of(self.weight)
        count,low,high = C.c_uint64(),C.c_uint64(),C.c_uint64()
        raw = Word();stats = (C.c_uint64*4)()
        status = self.lib.rc_bidi_search(self.handle,source,sink,C.byref(initial),C.byref(weight),self.price.buffer,ptr(self.slots),self.n,C.byref(count),C.byref(raw),C.byref(low),C.byref(high),stats)
        if status == 1:return None
        if status:raise RuntimeError(f'wide bidirectional status {status}; output rejected')
        return dict(slots=list(self.slots[:count.value]),raw=raw.integer(),objective=low.value+(high.value<<64),scanned_arcs=list(stats[:2]),settled_nodes=list(stats[2:]))

    def close(self):
        if getattr(self,'handle',None):self.lib.rc_bidi_destroy(self.handle);self.handle=None
        self.closed=True
    def __del__(self):self.close()

class Search:
    def __init__(self, fields, rc, binary):
        self.fields,self.rc=fields,rc
        try:
            self.forward=Forward(fields,rc,binary)
            self.bidirectional=Bidirectional(fields,rc,binary)
        except Exception:self.close();raise
    def prepare(self, prices, weight):
        self.forward.prepare(prices,weight)
        self.bidirectional.prepare(prices,weight)
    def search(self, source, sinks):
        targets=set(sinks)
        if len(targets)!=1:return self.forward.search(source,targets)
        sink=next(iter(targets));answer=self.bidirectional.search(source,sink)
        if answer is None:return {},{},set()
        u=source;parents={}
        for slot in answer['slots']:
            v=self.fields['dest_ranks'][slot]
            assert self.fields['row_offsets'][u]<=slot<self.fields['row_offsets'][u+1]
            assert v not in parents and v!=source
            parents[v]=(u,slot);u=v
        assert u==sink
        return {source:self.rc.initial(source),sink:answer['raw']},parents,{sink}
    def close(self):
        if hasattr(self,'forward'):self.forward.close()
        if hasattr(self,'bidirectional'):self.bidirectional.close()
    def __del__(self):self.close()
