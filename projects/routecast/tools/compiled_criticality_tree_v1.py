"""Exact compiled expansion, retaining the Python tree/seed/transaction semantics."""
from array import array
import ctypes as C
from fractions import Fraction
from pathlib import Path
from cached_multiplicative_occupancy_context_v1 import PriceView
from wide_cost_search_bridge_v2 import Word,Words,ptr

R=Path(__file__).resolve().parents[1]
BINARY=R/'build/compiled_criticality_tree_v2_2026-10-15/search.so'
U=C.c_uint64;P=C.POINTER(U);W=C.POINTER(Word)

class Result(C.Structure):
    _fields_=[('objective',U*4),('raw',Word),('attach',U),('count',U)]
assert C.sizeof(Result)==64


class NativePrices:
    """Borrow the serial, owner-excluded cost snapshot already used by fallback."""
    def __init__(self,base,snapshot):
        if type(snapshot) is not PriceView or snapshot.context.base is not base:
            raise ValueError('requires exact cached multiplicative snapshot and identical base')
        self.base,self.snapshot=base,snapshot
    def get(self,node,default=0):
        return self.base[node]+self.snapshot.get(node,0)
    def buffers(self,graph):
        s=self.snapshot;c=s.context;search=c.search
        if c.active!=s.ticket or search.closed or not search.prepared or not search.structural or search.weight!=1:
            raise RuntimeError('stale or incompatible native price context')
        if len(self.base)!=graph.n:
            raise ValueError('native price graph domain')
        if graph.base_owner is not self.base:
            if graph.base_owner is not None:raise ValueError('different node-base owner')
            graph.base=Words(self.base);graph.base_owner=self.base;graph.maxbase=max(self.base,default=0)
        prices=search.backends[1].forward.price
        if len(prices)!=graph.n:raise ValueError('price buffer domain')
        return graph.base,prices,graph.maxbase+search.price_ceiling


class Graph:
    def __init__(self,fields,increments,initial):
        self.closed=False;self.handle=None;self.base_owner=None
        self.offsets=array('Q',fields['row_offsets']);self.dest=array('Q',fields['dest_ranks'])
        self.inc=tuple(increments);self.initial=tuple(initial);self.n=len(self.initial)
        if (not self.n or len(self.offsets)!=self.n+1 or self.offsets[0]!=0
            or self.offsets[-1]!=len(self.dest) or len(self.inc)!=len(self.dest)
            or any(a>b for a,b in zip(self.offsets,self.offsets[1:]))
            or any(v>=self.n for v in self.dest)):
            raise ValueError('invalid CSR graph domain')
        if any(type(v) is not int or not 0<=v<2**128 for v in self.initial):
            raise ValueError('invalid initial raw cost')
        self.increments=Words(self.inc)
        self.raw_bound=max(self.initial)+self.n*max(self.inc,default=0)
        if self.raw_bound>=2**128:raise ValueError('raw simple-path domain exceeds 128 bits')
        self.zero=Words([0]*self.n);self.base=self.zero;self.maxbase=0
        self.path=array('Q',[0])*self.n;self.stats=(U*4)();self.result=Result()
        self.lib=C.CDLL(str(BINARY))
        self.lib.rc_criticality_create.argtypes=[U];self.lib.rc_criticality_create.restype=C.c_void_p
        self.lib.rc_criticality_destroy.argtypes=[C.c_void_p];self.lib.rc_criticality_destroy.restype=None
        self.lib.rc_criticality_expand.argtypes=[C.c_void_p,U,U,U,P,P,W,P,W,U,W,W,P,U,C.POINTER(Result),P]
        self.lib.rc_criticality_expand.restype=C.c_int
        self.handle=self.lib.rc_criticality_create(self.n)
        if not self.handle:raise MemoryError('compiled criticality workspace allocation failed')
        self.total_stats=[0,0,0];self.last_stats=None
    def tree(self,source):
        if self.closed or type(source) is not int or not 0<=source<self.n:raise ValueError('closed graph or invalid source')
        return Tree(self,source)
    def close(self):
        if getattr(self,'handle',None):self.lib.rc_criticality_destroy(self.handle);self.handle=None
        self.closed=True
    def __del__(self):self.close()


class Tree:
    def __init__(self,graph,source):
        self.graph=graph;self.source=source;self.n=graph.n
        self.offsets,self.dest,self.inc,self.initial=graph.offsets,graph.dest,graph.inc,graph.initial
        self.arrival={source:self.initial[source]};self.parents={}
    def expand(self,target,criticality,congestion,raw_budget):
        g=self.graph
        if g.closed:raise RuntimeError('closed graph')
        if type(target) is not int or not 0<=target<self.n:raise ValueError('target')
        if not isinstance(criticality,Fraction) or not 0<=criticality<=1:raise ValueError('criticality must be exact Fraction')
        if not hasattr(congestion,'get'):raise ValueError('sparse congestion getter required')
        if type(raw_budget) is not int or not 0<=raw_budget<2**128:raise ValueError('raw budget domain')
        p,q=criticality.numerator,criticality.denominator
        if max(p,q)>=2**64:raise ValueError('criticality denominator exceeds compiled domain')
        if type(congestion) is NativePrices:
            base,prices,ceiling=congestion.buffers(g)
        else:
            # Explicit dense adapter for generic primitive/reference tests.
            # Production uses the already prepared/patchable native snapshot.
            values=[congestion.get(n,0) for n in range(self.n)]
            prices=Words(values);base=g.zero;ceiling=max(values,default=0)
        if p*g.raw_bound+(q-p)*self.n*ceiling>=2**240:
            raise ValueError('weighted path envelope exceeds checked compiled domain')
        seeds=array('Q',self.arrival)
        raw=Words(self.arrival.values())
        status=g.lib.rc_criticality_expand(g.handle,target,p,q,ptr(g.offsets),ptr(g.dest),g.increments.buffer,
            ptr(seeds),raw.buffer,len(seeds),base.buffer,prices.buffer,ptr(g.path),self.n,C.byref(g.result),g.stats)
        g.last_stats=tuple(g.stats)
        for i in range(3):g.total_stats[i]+=g.stats[i]
        if status==1:return dict(status='UNREACHABLE',committed=False)
        if status:raise RuntimeError(f'compiled criticality failure {status}; tree unchanged')
        result=g.result;attach=result.attach;tail=tuple(g.path[:result.count]);value=result.raw.integer()
        prefix=[];v=attach
        while v!=self.source:
            parent,slot=self.parents[v];prefix.append(slot);v=parent
        prefix.reverse();path_slots=tuple(prefix)+tail
        answer=dict(status='COMMITTED' if value<=raw_budget else 'RETAIN_RAW_BUDGET',committed=value<=raw_budget,
                    raw=value,objective_numerator=sum(int(x)<<(64*i) for i,x in enumerate(result.objective)),
                    objective_denominator=q,attach=attach,new_nodes=len(tail),path_slots=path_slots)
        if value<=raw_budget:
            u=attach
            for slot in tail:
                v=self.dest[slot];self.parents[v]=(u,slot);self.arrival[v]=self.arrival[u]+self.inc[slot];u=v
        return answer
