"""Lazy region membership/adjacency filtering with the eager policy's semantics."""
from copy import copy
from hybrid_repair import RegionalSearch


class RegionAdjacency:
    def __init__(self,engine,locations,box,layer):
        self.engine=engine;self.locations=locations;self.box=box;self.layer=layer
        self.membership={};self.rows={};self.probes=0

    def inside(self,node):
        if node not in self.membership:
            xl,xh,yl,yh,layer=self.locations[node]
            self.membership[node]=(layer==self.layer and xl<=self.box[1] and xh>=self.box[0] and yl<=self.box[3] and yh>=self.box[2])
        return self.membership[node]

    def __getitem__(self,node):
        if node not in self.rows:
            if not self.inside(node):raise AssertionError('search expanded outside region')
            original=self.engine.adjacency[node];self.probes+=len(original)
            self.rows[node]=[eid for eid in original if self.inside(self.engine.graph.edges[eid].sink)]
        return self.rows[node]


class LazyRegionalSearch(RegionalSearch):
    def search(self,source,sinks):
        sinks=set(sinks);endpoints=[self.locations[n] for n in {source}|sinks]
        if len({loc[4] for loc in endpoints})!=1:raise ValueError('regional multi-layer repair unsupported')
        box=(min(loc[0] for loc in endpoints)-self.margin,max(loc[1] for loc in endpoints)+self.margin,
             min(loc[2] for loc in endpoints)-self.margin,max(loc[3] for loc in endpoints)+self.margin)
        adjacency=RegionAdjacency(self.engine,self.locations,box,endpoints[0][4])
        view=copy(self.engine);view.adjacency=adjacency
        result=view.search(source,sinks)
        if result.budget_exhausted:raise AssertionError('regional node budget unexpectedly exhausted')
        return result,{'box':box,'allowed_nodes':None,'region_node_tests':len(adjacency.membership),
                       'adjacency_filter_probes':adjacency.probes,'expanded_adjacency_rows':len(adjacency.rows),
                       'policy':'lazy region membership; total eligible nodes deliberately not enumerated'}
