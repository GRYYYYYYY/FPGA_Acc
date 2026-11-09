"""Raw-only p=q=1 adapter to existing compiled retained-tree kernel.
No all-node price allocation or new native kernel is introduced.
"""
from array import array
import ctypes as C
from wide_cost_search_bridge_v2 import Words,ptr

def expand(tree,target,raw_budget):
    self=tree;g=self.graph
    if g.closed:raise RuntimeError('closed graph')
    if type(target) is not int or not 0<=target<self.n:raise ValueError('target')
    if type(raw_budget) is not int or not 0<=raw_budget<2**128:raise ValueError('raw budget domain')
    if g.raw_bound>=2**128:raise ValueError('raw cost envelope')
    seeds=array('Q',self.arrival)
    raw=Words(self.arrival.values())
    status=g.lib.rc_criticality_expand(g.handle,target,1,1,ptr(g.offsets),ptr(g.dest),g.increments.buffer,
        ptr(seeds),raw.buffer,len(seeds),g.zero.buffer,g.zero.buffer,ptr(g.path),self.n,C.byref(g.result),g.stats)
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
                objective_denominator=1,attach=attach,new_nodes=len(tail),path_slots=path_slots)
    if value<=raw_budget:
        u=attach
        for slot in tail:
            v=self.dest[slot];self.parents[v]=(u,slot);self.arrival[v]=self.arrival[u]+self.inc[slot];u=v
    return answer
