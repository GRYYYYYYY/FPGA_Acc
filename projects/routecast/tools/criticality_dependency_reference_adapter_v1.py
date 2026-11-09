"""Full-model reference adapter; explicitly validates live price context on hits."""
from criticality_tree_dependency_cache_v1 import Graph as CachedGraph,Tree as CachedTree
from compiled_criticality_tree_v1 import NativePrices


class Tree(CachedTree):
    def expand(self,target,criticality,prices,raw_budget):
        if self.owner.closed:raise RuntimeError('closed dependency graph')
        if type(prices) is not NativePrices:raise ValueError('actual exact native-price view required')
        s=prices.snapshot;c=s.context;search=c.search
        if c.active!=s.ticket or search.closed or not search.prepared or not search.structural or search.weight!=1:
            raise RuntimeError('stale or incompatible price context')
        return super().expand(target,criticality,prices,raw_budget)


class Graph(CachedGraph):
    def __init__(self,fields,increments,initial):
        super().__init__(fields,increments,initial,entries=4096,read_limit=65536,state_limit=16384,total_limit=4*2**20)
        self.closed=False
    def tree(self,source):
        if self.closed:raise RuntimeError('closed dependency graph')
        base=super().tree(source);tree=Tree.__new__(Tree);tree.__dict__.update(base.__dict__);return tree
    def close(self):
        self.closed=True;self.cache.clear();self.items=0
