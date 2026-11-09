"""Exact cost-class memoization; objective identical to BoundNormalizedRCBase.

Includes source R for the Cinternal correction, destination R/C, complete
switch fields and native base cost. No path or target-dependent caching.
"""
from fractions import Fraction
from bound_indexed_cost import BoundIndexedCost
from path_rc import PathRC, State


class CachedBoundRCBase(BoundIndexedCost):
    def __init__(self, graph, text, bindings_csv, identity, scale=10**6):
        super().__init__(graph, text, bindings_csv, identity, scale)
        rc = PathRC(graph)
        if any(not s[0] for s in rc.switches.values()):
            raise ValueError('nonbuffered graph requires resistance state')
        cache = {}
        weights = []
        for eid, edge in enumerate(graph.edges):
            base = Fraction(self.rows[self.indices[edge.sink]]['base'])
            key = (rc.nodes[edge.source][0], rc.nodes[edge.sink],
                   rc.switches[edge.switch_id], base)
            if key not in cache:
                delay = rc.step(State(Fraction(0), Fraction(0)), eid).delay
                if delay < 0:
                    raise ValueError('negative RC increment')
                cache[key] = round((delay + base) / self.normalization * scale / 2)
            weights.append(cache[key])
        self.outgoing = {
            n: tuple((eid, dst, None if old is None else weights[eid])
                     for eid, dst, old in arcs)
            for n, arcs in self.outgoing.items()
        }
        self.cost_classes = len(cache)
