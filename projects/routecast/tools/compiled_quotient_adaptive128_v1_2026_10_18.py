"""Exact128 lane under the unchanged envelope, legacy256 fallback otherwise.
Both lanes preserve original A* ordering and result ABI. Experimental separate
module; no current model, kernel or factory changes.
"""
import ctypes as C
from array import array
from fractions import Fraction
from pathlib import Path
from compiled_quotient_criticality_astar_v1 import Graph as BaseGraph,Tree as BaseTree,BINARY as BASE_BINARY
from compiled_criticality_tree_v1 import NativePrices
from static_quotient_lower_bound_v1 import Snapshot
from wide_cost_search_bridge_v2 import Words,ptr
R=Path(__file__).resolve().parents[1]
BINARY=R/'build/quotient_adaptive128_v1_2026-10-18/search.so'
class Graph(BaseGraph):
 def __init__(self,lower):
  self.fast_handle=None;self.fast_unavailable=False;self.fast_calls=0;self.fallback_calls=0
  super().__init__(lower)
  self.fast_lib=C.CDLL(str(BINARY))
  self.fast_lib.rc_quotient128_create.argtypes=[C.c_uint64,C.c_uint64];self.fast_lib.rc_quotient128_create.restype=C.c_void_p
  self.fast_lib.rc_quotient128_destroy.argtypes=[C.c_void_p];self.fast_lib.rc_quotient128_destroy.restype=None
  self.fast_lib.rc_quotient128_expand.argtypes=self.lib.rc_quotient_expand.argtypes
  self.fast_lib.rc_quotient128_expand.restype=C.c_int
 def ensure_fast(self):
  if self.closed:raise RuntimeError('closed graph')
  if self.fast_handle:return True
  if self.fast_unavailable:return False
  self.fast_handle=self.fast_lib.rc_quotient128_create(self.n,self.lower.group_count)
  if not self.fast_handle:self.fast_unavailable=True
  return bool(self.fast_handle)
 def tree(self,source):
  result=super().tree(source);result.__class__=Tree;return result
 def close(self):
  if getattr(self,'fast_handle',None):self.fast_lib.rc_quotient128_destroy(self.fast_handle);self.fast_handle=None
  super().close()
class Tree(BaseTree):
    def expand(self, target, criticality, congestion, raw_budget):
        g = self.graph
        if g.closed or type(target) is not int or (not 0 <= target < self.n):
            raise ValueError('Closed graph or invalid target')
        if not isinstance(criticality, Fraction) or not 0 <= criticality <= 1:
            raise ValueError('Expected exact criticality')
        (p, q) = (criticality.numerator, criticality.denominator)
        if max(p, q) >= 2 ** 64 or type(raw_budget) is not int or (not 0 <= raw_budget < 2 ** 128):
            raise ValueError('Criticality/raw budget domain')
        if type(congestion) is NativePrices:
            (base, prices, ceiling) = g.native_buffers(congestion)
        elif type(congestion) is Snapshot and congestion.lower is g.lower:
            base = g.zero
            prices = Words(congestion.values)
            ceiling = max(congestion.values, default=0)
        else:
            raise ValueError('Requires certified native or immutable complete-price snapshot')
        table = g.table(target)
        envelope = p * g.raw_bound + (q - p) * self.n * ceiling + p * table.maxraw + (q - p) * table.maxfloor
        if envelope >= 2 ** 240:
            raise ValueError('Weighted cost+potential envelope exceeds240 bits')
        seeds = array('Q', self.arrival)
        raw = Words(self.arrival.values())
        if envelope < 2 ** 127 and g.ensure_fast():
            handle = g.fast_handle
            expand_fn = g.fast_lib.rc_quotient128_expand
            g.fast_calls += 1
        else:
            handle = g.handle
            expand_fn = g.lib.rc_quotient_expand
            g.fallback_calls += 1
        status = expand_fn(handle, target, p, q, ptr(g.offsets), ptr(g.dest), g.increments.buffer, ptr(seeds), raw.buffer, len(seeds), base.buffer, prices.buffer, ptr(g.path), self.n, C.byref(g.result), g.stats, ptr(g.groups), ptr(table.raw), ptr(table.floor), ptr(table.reachable))
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
class RawFloorTree(Tree):
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
        envelope = p * g.raw_bound + (q - p) * self.n * ceiling + p * table.maxraw + (q - p) * table.maxfloor
        if envelope >= 2 ** 240:
            raise ValueError('Weighted cost+potential envelope exceeds240 bits')
        seeds = array('Q', self.arrival)
        raw = Words(self.arrival.values())
        if envelope < 2 ** 127 and g.ensure_fast():
            handle = g.fast_handle
            expand_fn = g.fast_lib.rc_quotient128_expand
            g.fast_calls += 1
        else:
            handle = g.handle
            expand_fn = g.lib.rc_quotient_expand
            g.fallback_calls += 1
        status = expand_fn(handle, target, p, q, ptr(g.offsets), ptr(g.dest), g.increments.buffer, ptr(seeds), raw.buffer, len(seeds), base.buffer, prices.buffer, ptr(g.path), self.n, C.byref(g.result), g.stats, ptr(g.groups), ptr(table.raw), ptr(table.floor), ptr(table.reachable))
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
def raw_tree(graph,source):
 result=graph.tree(source);result.__class__=RawFloorTree;return result
