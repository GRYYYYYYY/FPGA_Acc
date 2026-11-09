"""Exact raw-only initial floor pilot, same compiled A* kernel.
No graph mutation or congestion/budget law changes. Tree prefixes are retained
only after exact unconstrained raw shortest-path expansion. Equal-cost paths
may differ from a Dijkstra floor engine; floors must independently agree.
"""
import ctypes as C
from array import array
from fractions import Fraction
from compiled_quotient_criticality_astar_v1 import Tree as BaseTree
from wide_cost_search_bridge_v2 import Words,ptr

class RawFloorTree(BaseTree):
    def expand(self, target):
        criticality = Fraction(1, 1)
        raw_budget = self.graph.raw_bound
        g = self.graph
        if g.closed or type(target) is not int or (not 0 <= target < self.n):
            raise ValueError('Closed graph or invalid target')
        if not isinstance(criticality, Fraction) or not 0 <= criticality <= 1:
            raise ValueError('Expected exact criticality')
        (p, q) = (criticality.numerator, criticality.denominator)
        if max(p, q) >= 2 ** 64 or type(raw_budget) is not int or (not 0 <= raw_budget < 2 ** 128):
            raise ValueError('Criticality/raw budget domain')
        base = g.zero
        prices = g.zero
        ceiling = 0
        table = g.table(target)
        if p * g.raw_bound + (q - p) * self.n * ceiling + p * table.maxraw + (q - p) * table.maxfloor >= 2 ** 240:
            raise ValueError('Weighted cost+potential envelope exceeds240 bits')
        seeds = array('Q', self.arrival)
        raw = Words(self.arrival.values())
        status = g.lib.rc_quotient_expand(g.handle, target, p, q, ptr(g.offsets), ptr(g.dest), g.increments.buffer, ptr(seeds), raw.buffer, len(seeds), base.buffer, prices.buffer, ptr(g.path), self.n, C.byref(g.result), g.stats, ptr(g.groups), ptr(table.raw), ptr(table.floor), ptr(table.reachable))
        g.last_stats = tuple(g.stats)
        for i in range(3):
            g.total_stats[i] += g.stats[i]
        if status == 1:
            return dict(status='UNREACHABLE', committed=False)
        if status:
            raise RuntimeError(f'Compiled quotient A* failed:{status}; tree unchanged')
        result = g.result
        attach = result.attach
        tail = tuple(g.path[:result.count])
        value = result.raw.integer()
        prefix = []
        v = attach
        while v != self.source:
            (parent, slot) = self.parents[v]
            prefix.append(slot)
            v = parent
        prefix.reverse()
        path = tuple(prefix) + tail
        committed = value <= raw_budget
        answer = dict(status='COMMITTED' if committed else 'RETAIN_RAW_BUDGET', committed=committed, raw=value, objective_numerator=sum((int(x) << 64 * i for (i, x) in enumerate(result.objective))), objective_denominator=q, attach=attach, new_nodes=len(tail), path_slots=path)
        if committed:
            u = attach
            for slot in tail:
                v = self.dest[slot]
                self.parents[v] = (u, slot)
                self.arrival[v] = self.arrival[u] + self.inc[slot]
                u = v
        return answer

def tree(graph,source):
    result=graph.tree(source)
    result.__class__=RawFloorTree
    return result
