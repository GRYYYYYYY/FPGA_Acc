"""CPU-only connection-state oracle; graph/cost context is immutable.

Edge occupancy is deliberately a toy accounting model, not VPR RR occupancy.
Search minimizes (frozen path cost, hop count, edge-ID sequence), allowing
same-coordinate transitions and detours. No congestion-driven rerouting.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional

UINT32_MAX = (1 << 32) - 1
UINT64_MAX = (1 << 64) - 1


@dataclass(frozen=True)
class Edge:
    source: int
    sink: int
    cost: int = 1
    capacity: int = 1


@dataclass(frozen=True)
class Connection:
    source: int
    sink: int
    demand_q: int
    path: tuple[int, ...]


@dataclass(frozen=True)
class State:
    epoch: int
    connection: Optional[Connection]


class Result(Enum):
    COMMITTED = 'committed'
    STALE = 'stale'
    INVALID = 'invalid'
    NO_PATH = 'no_path'
    OVERFLOW = 'overflow'


def integer(value, lower, upper):
    return type(value) is int and lower <= value <= upper


class Golden:
    def __init__(self, node_count, edges, hop_limit=256):
        if not integer(node_count, 1, UINT32_MAX) or not integer(hop_limit, 0, 256):
            raise ValueError('invalid graph bounds')
        self.node_count = node_count
        self.edges = tuple(edges)
        self.hop_limit = hop_limit
        self.adjacency = [[] for _ in range(node_count)]
        for index, edge in enumerate(self.edges):
            if (not isinstance(edge, Edge) or
                not integer(edge.source, 0, node_count-1) or
                not integer(edge.sink, 0, node_count-1) or
                not integer(edge.cost, 0, UINT32_MAX) or
                not integer(edge.capacity, 0, UINT32_MAX)):
                raise ValueError('invalid edge')
            self.adjacency[edge.source].append(index)
        self.adjacency = tuple(tuple(row) for row in self.adjacency)
        self._states = {}
        self._demand = [0] * len(self.edges)

    @property
    def demand(self):
        return tuple(self._demand)

    @property
    def states(self):
        return dict(self._states)

    def path(self, source, sink):
        """Layered dynamic programming: one best prefix per (node, hops).

        Nonnegative costs plus hop-count tie breaking imply a cycle-free optimum.
        Keeping layers separate is necessary when hop budget constrains search.
        """
        if not integer(source, 0, self.node_count-1) or not integer(sink, 0, self.node_count-1):
            raise ValueError('invalid endpoint')
        layer = {source: (0, ())}
        best = (0, 0, ()) if source == sink else None
        for hops in range(1, self.hop_limit + 1):
            following = {}
            for node, (cost, prefix) in layer.items():
                for eid in self.adjacency[node]:
                    edge = self.edges[eid]
                    if edge.capacity == 0:
                        continue
                    candidate = (cost + edge.cost, prefix + (eid,))
                    previous = following.get(edge.sink)
                    if previous is None or candidate < previous:
                        following[edge.sink] = candidate
            layer = following
            if sink in layer:
                cost, prefix = layer[sink]
                candidate = (cost, hops, prefix)
                if best is None or candidate < best:
                    best = candidate
            if not layer:
                break
        return None if best is None else best[2]

    def update(self, connection_id, epoch, source=None, sink=None, demand_q=None, *, remove=False):
        """Atomic upsert/remove; epoch is monotone per ID, starting at 1.

        Failed operations consume no epoch. Removal retains a tombstone, including
        removal of an unknown ID. No batch-wide transaction is implied.
        """
        if (not integer(connection_id, 0, UINT64_MAX) or
            not integer(epoch, 1, UINT64_MAX) or type(remove) is not bool):
            return Result.INVALID
        previous = self._states.get(connection_id)
        if previous is not None and epoch <= previous.epoch:
            return Result.STALE
        replacement = None
        if remove:
            if source is not None or sink is not None or demand_q is not None:
                return Result.INVALID
        else:
            if (not integer(source, 0, self.node_count-1) or
                not integer(sink, 0, self.node_count-1) or
                not integer(demand_q, 0, UINT32_MAX)):
                return Result.INVALID
            path = self.path(source, sink)
            if path is None:
                return Result.NO_PATH
            replacement = Connection(source, sink, demand_q, path)
        delta = {}
        if previous is not None and previous.connection is not None:
            for eid in previous.connection.path:
                delta[eid] = delta.get(eid, 0) - previous.connection.demand_q
        if replacement is not None:
            for eid in replacement.path:
                delta[eid] = delta.get(eid, 0) + replacement.demand_q
        values = {eid: self._demand[eid] + value for eid, value in delta.items()}
        if any(value > UINT32_MAX for value in values.values()):
            return Result.OVERFLOW
        if any(value < 0 for value in values.values()):
            raise AssertionError('internal occupancy underflow')
        for eid, value in values.items():
            self._demand[eid] = value
        self._states[connection_id] = State(epoch, replacement)
        return Result.COMMITTED

    def rebuild(self):
        """Full reroute of active endpoints under the same frozen context."""
        demand = [0] * len(self.edges)
        for state in self._states.values():
            if state.connection is None:
                continue
            connection = state.connection
            path = self.path(connection.source, connection.sink)
            if path is None or path != connection.path:
                raise AssertionError('stored path differs from frozen-context reroute')
            for eid in path:
                demand[eid] += connection.demand_q
        return tuple(demand)
