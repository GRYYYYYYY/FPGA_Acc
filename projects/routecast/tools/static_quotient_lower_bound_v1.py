"""Immutable directed quotient lower bounds for raw plus node-price objectives.

The two reverse distances can use different abstract paths: their nonnegative
weighted sum is still consistent on every original arc. Static group merging
may weaken the bound, never remove original paths. No native labels are used.
"""
import heapq
from collections import OrderedDict
from fractions import Fraction

from criticality_shared_tree_sparse_reference_v3 import Graph as ReferenceGraph


class Projection:
    def __init__(self, groups, tables, criticality):
        self.groups, (self.raw, self.price) = groups, tables
        self.p, self.q = criticality.numerator, criticality.denominator
        self.cache = {}

    def __getitem__(self, node):
        group = self.groups[node]
        if group not in self.cache:
            self.cache[group] = (None if self.raw[group] is None else
                                 self.p*self.raw[group]+(self.q-self.p)*self.price[group])
        return self.cache[group]


class Snapshot:
    def __init__(self, lower, values):
        values = tuple(values)
        if len(values) != lower.n or any(type(v) is not int or v < f for v, f in zip(values, lower.floor)):
            raise ValueError('Complete stable prices must dominate the certified node floor')
        self.lower, self.values = lower, values

    def get(self, node, default=0):
        return self.values[node]


class LowerBound:
    def __init__(self, fields, increments, initial, floor, groups, max_targets=64):
        reference = ReferenceGraph(fields, increments, initial)
        self.graph = reference._snapshot
        self.n = self.graph['n']
        self.floor, self.groups = tuple(floor), tuple(groups)
        if (len(self.floor) != self.n or len(self.groups) != self.n
                or any(type(v) is not int or v < 0 for v in self.floor)
                or any(type(v) is not int or v < 0 for v in self.groups)
                or type(max_targets) is not int or max_targets < 1):
            raise ValueError('Invalid floor, groups or cache bound')
        unique = sorted(set(self.groups))
        if unique != list(range(len(unique))):
            raise ValueError('Group IDs must form a dense domain')
        self.group_count = len(unique)
        minima = {}
        for u in range(self.n):
            a = self.groups[u]
            for slot in range(self.graph['offsets'][u], self.graph['offsets'][u+1]):
                v = self.graph['dest'][slot]
                b = self.groups[v]
                if a == b:
                    continue
                key = a, b
                raw, price = self.graph['inc'][slot], self.floor[v]
                if key in minima:
                    old_raw, old_price = minima[key]
                    raw, price = min(raw, old_raw), min(price, old_price)
                minima[key] = raw, price
        self.abstract_arcs = len(minima)
        self.reverse = [[] for _ in unique]
        for (a, b), (raw, price) in sorted(minima.items()):
            self.reverse[b].append((a, raw, price))
        self.max_targets = max_targets
        self.cache = OrderedDict()
        self.table_builds = self.cache_hits = self.evictions = 0

    def tables(self, target):
        if type(target) is not int or not 0 <= target < self.n:
            raise ValueError('Invalid target')
        group = self.groups[target]
        if group in self.cache:
            self.cache_hits += 1
            self.cache.move_to_end(group)
            return self.cache[group]
        results = []
        for column in (1, 2):
            distance = [None]*self.group_count
            distance[group] = 0
            pending = [(0, group)]
            while pending:
                value, node = heapq.heappop(pending)
                if distance[node] != value:
                    continue
                for edge in self.reverse[node]:
                    previous = edge[0]
                    candidate = value+edge[column]
                    if distance[previous] is None or candidate < distance[previous]:
                        distance[previous] = candidate
                        heapq.heappush(pending, (candidate, previous))
            results.append(tuple(distance))
        assert all((a is None) == (b is None) for a, b in zip(*results))
        self.table_builds += 1
        value = tuple(results)
        self.cache[group] = value
        if len(self.cache) > self.max_targets:
            self.cache.popitem(last=False)
            self.evictions += 1
        return value

    def heuristic(self, target, criticality):
        if not isinstance(criticality, Fraction) or not 0 <= criticality <= 1:
            raise ValueError('Expected exact criticality in[0,1]')
        return Projection(self.groups, self.tables(target), criticality)


class Graph:
    def __init__(self, lower):
        self.lower = lower
        self.reference = ReferenceGraph.__new__(ReferenceGraph)
        self.reference._snapshot = lower.graph
        self.settled = self.scanned = self.pushes = 0

    def tree(self, source):
        tree = self.reference.tree(source)
        tree.__class__ = Tree
        tree.owner = self
        return tree


class Tree:
    def expand(self, target, criticality, congestion, raw_budget):
        owner, lower = self.owner, self.owner.lower
        if type(target) is not int or not 0 <= target < self.n:
            raise ValueError('Invalid target')
        if type(raw_budget) is not int or raw_budget < 0:
            raise ValueError('Invalid raw budget')
        if not isinstance(congestion, Snapshot) or congestion.lower is not lower:
            raise ValueError('Requires a validated immutable complete-price snapshot')
        h = lower.heuristic(target, criticality)
        p, q = criticality.numerator, criticality.denominator
        distance = {u: p*raw for u, raw in self.arrival.items() if h[u] is not None}
        pending = [(cost+h[u], cost, u) for u, cost in distance.items()]
        heapq.heapify(pending)
        owner.pushes += len(pending)
        previous, visited = {}, set()
        while pending:
            _, cost, u = heapq.heappop(pending)
            if u in visited or distance[u] != cost:
                continue
            visited.add(u)
            owner.settled += 1
            if u == target:
                break
            for slot in range(self.offsets[u], self.offsets[u+1]):
                owner.scanned += 1
                v = self.dest[slot]
                if v in self.arrival or v in visited or h[v] is None:
                    continue
                candidate = cost+p*self.inc[slot]+(q-p)*congestion.values[v]
                if candidate < distance.get(v, candidate+1):
                    distance[v] = candidate
                    previous[v] = u, slot
                    heapq.heappush(pending, (candidate+h[v], candidate, v))
                    owner.pushes += 1
        if target not in visited:
            return dict(status='UNREACHABLE', committed=False)
        new = []
        u = target
        while u not in self.arrival:
            parent, slot = previous[u]
            new.append((u, parent, slot))
            u = parent
        attach = u
        raw = self.arrival[u]+sum(self.inc[slot] for _, _, slot in new)
        path = []
        while u != self.source:
            parent, slot = self.parents[u]
            path.append(slot)
            u = parent
        path.reverse()
        path.extend(slot for _, _, slot in reversed(new))
        committed = raw <= raw_budget
        result = dict(status='COMMITTED' if committed else 'RETAIN_RAW_BUDGET', committed=committed,
                      raw=raw, objective_numerator=distance[target], objective_denominator=q,
                      attach=attach, new_nodes=len(new), path_slots=tuple(path))
        if committed:
            for v, parent, slot in reversed(new):
                self.parents[v] = parent, slot
                self.arrival[v] = self.arrival[parent]+self.inc[slot]
        return result
