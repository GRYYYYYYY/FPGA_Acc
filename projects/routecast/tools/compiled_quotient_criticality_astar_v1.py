"""Separate checked256-bit A* bridge; original compiled/model code stays frozen."""
import ctypes as C
from array import array
from collections import OrderedDict
from fractions import Fraction

from compiled_criticality_tree_v1 import Graph as OriginalGraph, Tree as OriginalTree, NativePrices, Result
from wide_cost_search_bridge_v2 import Words, Word, ptr
from static_quotient_lower_bound_v1 import Snapshot
from cached_multiplicative_occupancy_context_v1 import Context as BaselineContext
from scaled_present_multiplicative_context_v1 import Context as ScaledContext
from native_price_buffer_store_v1 import Store
from pathlib import Path

R=Path(__file__).resolve().parents[1]
BINARY=R/'build/compiled_quotient_criticality_astar_v1_2026-10-17/search.so'
U=C.c_uint64;P=C.POINTER(U);W=C.POINTER(Word)


class Tables:
    def __init__(self, raw, floor):
        self.raw=array('Q');self.floor=array('Q')
        self.reachable=array('Q');self.maxraw=self.maxfloor=0
        for a,b in zip(raw,floor):
            if (a is None)!=(b is None):raise ValueError('inconsistent abstract reachability')
            self.reachable.append(a is not None)
            a,b=(0,0) if a is None else (a,b)
            if any(type(v) is not int or not 0<=v<2**240 for v in (a,b)):
                raise ValueError('potential outside240-bit input domain')
            self.maxraw=max(self.maxraw,a);self.maxfloor=max(self.maxfloor,b)
            for i in range(4):
                self.raw.append((a>>(64*i))&((1<<64)-1))
                self.floor.append((b>>(64*i))&((1<<64)-1))


class Graph(OriginalGraph):
    def __init__(self, lower):
        self.astar=False
        self.lower=lower
        f=lower.graph
        super().__init__(dict(row_offsets=f['offsets'],dest_ranks=f['dest']),f['inc'],f['initial'])
        # Reuse the exact validated CSR/128-bit raw/seed ABI. Release the unused
        # old workspace before allocating A*, and retain its elapsed setup cost.
        self.lib.rc_criticality_destroy(self.handle);self.handle=None
        self.lib=C.CDLL(str(BINARY));self.astar=True
        self.lib.rc_quotient_create.argtypes=[U,U];self.lib.rc_quotient_create.restype=C.c_void_p
        self.lib.rc_quotient_destroy.argtypes=[C.c_void_p];self.lib.rc_quotient_destroy.restype=None
        self.lib.rc_quotient_expand.argtypes=[C.c_void_p,U,U,U,P,P,W,P,W,U,W,W,P,U,C.POINTER(Result),P,P,P,P,P]
        self.lib.rc_quotient_expand.restype=C.c_int
        self.handle=self.lib.rc_quotient_create(self.n,lower.group_count)
        if not self.handle:raise MemoryError('compiled A* workspace')
        self.groups=array('Q',lower.groups);self.tables=OrderedDict();self.native_guard=None

    def table(self,target):
        key=self.lower.groups[target]
        if key in self.tables:
            self.tables.move_to_end(key);return self.tables[key]
        item=Tables(*self.lower.tables(target));self.tables[key]=item
        if len(self.tables)>self.lower.max_targets:self.tables.popitem(last=False)
        return item

    def native_buffers(self,congestion):
        c=congestion.snapshot.context
        if type(c) not in (BaselineContext,ScaledContext) or type(c.search) is not Store:
            raise ValueError('Unsupported context/store for native floor certificate')
        # Original active ticket/store checks execute even for a cached table or
        # an already-owned target needing no edge reads.
        buffers=congestion.buffers(self)
        if type(c) is ScaledContext and (type(c.present_factor) is not int or c.present_factor not in (1,2,4)):
            raise ValueError('Invalid present factor')
        if self.native_guard is None:
            if self.lower.floor!=tuple(c.base[n]+c.weight*c.spans[n] for n in range(self.n)):
                raise ValueError('Native context does not certify the static floor')
            self.native_guard=(c,c.base,c.spans,c.weight)
        else:
            old,base,spans,weight=self.native_guard
            if c is not old or c.base is not base or c.spans is not spans or c.weight!=weight:
                raise ValueError('Static floor context identity/weight changed; rebuild required')
        return buffers

    def tree(self,source):
        t=super().tree(source);t.__class__=Tree;return t

    def close(self):
        if getattr(self,'handle',None):
            if self.astar:self.lib.rc_quotient_destroy(self.handle)
            else:self.lib.rc_criticality_destroy(self.handle)
            self.handle=None
        self.closed=True


class Tree(OriginalTree):
    def expand(self,target,criticality,congestion,raw_budget):
        g=self.graph
        if g.closed or type(target) is not int or not 0<=target<self.n:
            raise ValueError('Closed graph or invalid target')
        if not isinstance(criticality,Fraction) or not 0<=criticality<=1:
            raise ValueError('Expected exact criticality')
        p,q=criticality.numerator,criticality.denominator
        if max(p,q)>=2**64 or type(raw_budget) is not int or not 0<=raw_budget<2**128:
            raise ValueError('Criticality/raw budget domain')
        if type(congestion) is NativePrices:
            base,prices,ceiling=g.native_buffers(congestion)
        elif type(congestion) is Snapshot and congestion.lower is g.lower:
            base=g.zero;prices=Words(congestion.values);ceiling=max(congestion.values,default=0)
        else:raise ValueError('Requires certified native or immutable complete-price snapshot')
        table=g.table(target)
        if p*g.raw_bound+(q-p)*self.n*ceiling+p*table.maxraw+(q-p)*table.maxfloor>=2**240:
            raise ValueError('Weighted cost+potential envelope exceeds240 bits')
        seeds=array('Q',self.arrival);raw=Words(self.arrival.values())
        status=g.lib.rc_quotient_expand(g.handle,target,p,q,ptr(g.offsets),ptr(g.dest),g.increments.buffer,
            ptr(seeds),raw.buffer,len(seeds),base.buffer,prices.buffer,ptr(g.path),self.n,
            C.byref(g.result),g.stats,ptr(g.groups),ptr(table.raw),ptr(table.floor),ptr(table.reachable))
        g.last_stats=tuple(g.stats)
        for i in range(3):g.total_stats[i]+=g.stats[i]
        if status==1:return dict(status='UNREACHABLE',committed=False)
        if status:raise RuntimeError(f'Compiled quotient A* failed:{status}; tree unchanged')
        result=g.result;attach=result.attach;tail=tuple(g.path[:result.count]);value=result.raw.integer()
        prefix=[];v=attach
        while v!=self.source:
            parent,slot=self.parents[v];prefix.append(slot);v=parent
        prefix.reverse();path=tuple(prefix)+tail
        committed=value<=raw_budget
        answer=dict(status='COMMITTED' if committed else 'RETAIN_RAW_BUDGET',committed=committed,
                    raw=value,objective_numerator=sum(int(x)<<(64*i) for i,x in enumerate(result.objective)),
                    objective_denominator=q,attach=attach,new_nodes=len(tail),path_slots=path)
        if committed:
            u=attach
            for slot in tail:
                v=self.dest[slot];self.parents[v]=(u,slot);self.arrival[v]=self.arrival[u]+self.inc[slot];u=v
        return answer
