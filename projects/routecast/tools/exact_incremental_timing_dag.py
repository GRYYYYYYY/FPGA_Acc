"""Exact Fraction DAG arrivals with transactional sparse delay changes."""
from collections import defaultdict, deque
from fractions import Fraction
import heapq


class ExactTimingDAG:
    def __init__(self, nodes, edges, sinks, budgets):
        self.budgets = {str(k): Fraction(v) for k, v in budgets.items()}
        self.incoming = {n: [] for n in nodes}
        self.outgoing = {n: [] for n in nodes}
        self.targets = defaultdict(set)
        indegree = dict.fromkeys(self.incoming, 0)
        for u, v, offset, connection in edges:
            offset = Fraction(offset)
            connection = None if connection is None else str(connection)
            if connection is not None and connection not in self.budgets:
                raise ValueError('missing connection budget')
            self.incoming[v].append((u, offset, connection))
            self.outgoing[u].append(v)
            indegree[v] += 1
            if connection is not None:
                self.targets[connection].add(v)
        queue = deque(n for n in indegree if not indegree[n])
        self.order = []
        while queue:
            u = queue.popleft()
            self.order.append(u)
            for v in self.outgoing[u]:
                indegree[v] -= 1
                if not indegree[v]:
                    queue.append(v)
        if len(self.order) != len(indegree):
            raise ValueError('timing graph is cyclic')
        self.rank = {n: i for i, n in enumerate(self.order)}
        self.sinks = tuple(sinks)
        if not self.sinks or any(n not in self.incoming for n in self.sinks):
            raise ValueError('invalid sinks')
        self.arrivals = {}
        for n in self.order:
            self.arrivals[n] = self._arrival(n)

    def _arrival(self, n):
        return max([Fraction(0)] + [self.arrivals[u] + offset +
                   (self.budgets[c] if c is not None else 0)
                   for u, offset, c in self.incoming[n]])

    @property
    def cpd(self):
        return max(self.arrivals[n] for n in self.sinks)

    def update(self, changes, *, commit=False):
        """Return trial CPD; restore all state unless explicitly committed."""
        changes = {str(k): Fraction(v) for k, v in changes.items()}
        if any(k not in self.budgets or v < 0 for k, v in changes.items()):
            raise ValueError('invalid budget update')
        old_budgets = {k: self.budgets[k] for k in changes}
        old_arrivals = {}
        success = False
        try:
            pending = set()
            heap = []
            def enqueue(n):
                if n not in pending:
                    pending.add(n)
                    heapq.heappush(heap, self.rank[n])
            for k, v in changes.items():
                if self.budgets[k] != v:
                    self.budgets[k] = v
                    for n in self.targets[k]:
                        enqueue(n)
            while heap:
                n = self.order[heapq.heappop(heap)]
                pending.remove(n)
                value = self._arrival(n)
                if value != self.arrivals[n]:
                    old_arrivals.setdefault(n, self.arrivals[n])
                    self.arrivals[n] = value
                    for v in self.outgoing[n]:
                        enqueue(v)
            result = self.cpd
            success = True
            return result
        finally:
            if not commit or not success:
                self.budgets.update(old_budgets)
                self.arrivals.update(old_arrivals)

    @classmethod
    def from_native_metadata(cls, graph, mapping, metadata, budgets):
        edges = []
        for eid, e in graph['edges'].items():
            if e['disabled']:
                continue
            c = metadata['edge_connection_ids'].get(eid)
            offset = (Fraction(mapping['external_edges'][eid]['old_local_offset_seconds'])
                      if c is not None else Fraction(e['max_delay_seconds'])) * 10**9
            edges.append((e['source'], e['sink'], offset, c))
        return cls([int(n) for n in graph['nodes']], edges,
                   [int(n) for n, kind in graph['nodes'].items() if kind == 'SINK'], budgets)
