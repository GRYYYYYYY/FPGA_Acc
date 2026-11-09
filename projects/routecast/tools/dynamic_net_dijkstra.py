"""Positive dynamic-cost multi-sink search; caller authenticates fixed CSR/state."""
import heapq
from types import MappingProxyType
from prepared_csr import U64


def search(fields, source, sinks, own_nodes, occupancy):
    sinks = frozenset(sinks)
    if type(source) is not int or not 0 <= source < len(fields['node_ids']):
        raise ValueError('invalid source')
    if any(type(n) is not int or not 0 <= n < len(fields['node_ids']) for n in sinks):
        raise ValueError('invalid sink')
    remaining = set(sinks)
    distance, parent, settled = {source: 0}, {}, {}
    heap = [(0, source)]
    results = {}
    examined = 0
    while heap and remaining:
        cost, node = heapq.heappop(heap)
        if distance.get(node) != cost:
            continue
        settled[node] = cost
        if node in remaining:
            path, cursor = [], node
            while cursor != source:
                previous, edge = parent[cursor]
                path.append(edge)
                cursor = previous
            results[node] = ('FOUND', cost, tuple(reversed(path)))
            remaining.remove(node)
            if not remaining:
                break
        for slot in range(fields['row_offsets'][node], fields['row_offsets'][node+1]):
            examined += 1
            dest = fields['dest_ranks'][slot]
            scalar = int(fields['costs'][slot])
            if scalar == U64 or fields['capacities'][dest] <= 0:
                continue
            other = occupancy.get(dest, 0)-(dest in own_nodes)
            if scalar <= 0 or type(other) is not int or other < 0:
                raise ValueError('positive scalar and nonnegative integer otherNET demand required')
            candidate = cost+scalar*(1+other)
            if candidate < distance.get(dest, float('inf')):
                distance[dest] = candidate
                parent[dest] = (node, fields['edge_ids'][slot])
                heapq.heappush(heap, (candidate, dest))
    for sink in remaining:
        results[sink] = ('UNREACHABLE', None, None)
    # For any found sink of cost C, min(settled.get(n,C),C) is its feasible potential.
    return results, MappingProxyType(settled), examined
