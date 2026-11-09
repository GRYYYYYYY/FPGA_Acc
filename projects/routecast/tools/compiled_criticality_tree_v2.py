"""Same compiled search and tree updates; reusable immutable dense-price adapter."""
from array import array
import ctypes as C
from fractions import Fraction
from compiled_criticality_tree_v1 import Graph as _Graph, Tree as _Tree, NativePrices, BINARY, Words, ptr
class FrozenPrices:
    __slots__=('_values','_buffer','_maximum','_sealed')
    def __init__(self,values):
        values=tuple(values)
        if not values or any(type(v) is not int or not 0<=v<2**128 for v in values):raise ValueError('frozen price domain')
        object.__setattr__(self,'_values',values)
        object.__setattr__(self,'_buffer',Words(values))
        object.__setattr__(self,'_maximum',max(values))
        object.__setattr__(self,'_sealed',True)
    def __setattr__(self,key,value):raise AttributeError('immutable price snapshot')
    @property
    def values(self):return self._values
    def get(self,node,default=0):
        if type(node) is not int or not 0<=node<len(self._values):raise ValueError('frozen price node')
        return self._values[node]
    def buffers(self,graph):
        if graph.closed or graph.n!=len(self._values):raise ValueError('frozen price graph domain')
        return graph.zero,self._buffer,self._maximum
class Graph(_Graph):
    def tree(self,source):
        if self.closed or type(source) is not int or not 0<=source<self.n:raise ValueError('closed graph or invalid source')
        return Tree(self,source)
class Tree(_Tree):
    def expand(self,target,criticality,congestion,raw_budget):
        g=self.graph
        if g.closed:raise RuntimeError('closed graph')
        if type(target) is not int or not 0<=target<self.n:raise ValueError('target')
        if not isinstance(criticality,Fraction) or not 0<=criticality<=1:raise ValueError('criticality must be exact Fraction')
        if not hasattr(congestion,'get'):raise ValueError('sparse congestion getter required')
        if type(raw_budget) is not int or not 0<=raw_budget<2**128:raise ValueError('raw budget domain')
        p,q=criticality.numerator,criticality.denominator
        if max(p,q)>=2**64:raise ValueError('criticality denominator exceeds compiled domain')
        if type(congestion) in (NativePrices,FrozenPrices):
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
