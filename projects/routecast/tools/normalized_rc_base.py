"""Label-independent equal-weight RC+native-base objective, seconds normalized.

This is constant criticality=1/2, not per-pin native criticality parity. No
present/history congestion, route-tree starts or lookahead. Supports the same
single-segment base table mapping and all-buffered/nonnegative RC restrictions.
"""
from fractions import Fraction
from native_indexed_cost import NativeBaseSketch,parse_cost_echo
from path_rc import PathRC,State

class NormalizedRCBaseSketch(NativeBaseSketch):
    def __init__(self,graph,text,table_graph_sha256,scale=10**6):
        super().__init__(graph,text,table_graph_sha256,scale)
        norm,rows=parse_cost_echo(text);norm=Fraction(norm)
        base={row['type']:Fraction(row['base'])/norm for row in rows.values()}
        rc=PathRC(graph)
        if any(not switch[0] for switch in rc.switches.values()):raise ValueError('nonbuffered graph requires resistance state')
        weights={}
        for eid,edge in enumerate(graph.edges):
            delay=rc.step(State(Fraction(0),Fraction(0)),eid).delay
            if delay<0:raise ValueError('negative RC increment')
            weights[eid]=round((delay/norm+base[graph.nodes[edge.sink].type])*scale/2)
        self.outgoing={n:tuple((eid,dst,None if weight is None else weights[eid]) for eid,dst,weight in arcs) for n,arcs in self.outgoing.items()}
        del self.node_costs
        self.scale=scale
        self.normalization=norm
