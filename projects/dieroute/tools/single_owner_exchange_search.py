"""Exact delay-only CSR search allowing one globally released owner.

This is a CPU research primitive, not a transaction or a production router.
Source ownership must already follow the caller's source-exclusion contract.
No hop bound, corridor, negotiated cost or displaced-net repair is modeled.
"""
from heapq import heappop, heappush
from itertools import count


def search(nodes, edges, capacities, owners, source, sink, target_owner,
           maximum_delay, suffix_lower_bound=None):
    """Return cheapest source-sink path with at most one other owner removed.

    State is (vertex, released_owner). The release is chosen only when a
    full resource is entered. An already chosen owner remains released
    everywhere. Nonnegative edge delays and immutable occupancy are required.
    An optional suffix potential must be a valid nonnegative lower bound;
    the caller owns its proof. No posterior list of candidate owners is used.
    """
    if maximum_delay < 0:
        raise ValueError('maximum_delay must be nonnegative')
    if not (len(nodes) == len(capacities) == len(owners)):
        raise ValueError('node, capacity and owner dimensions differ')
    if not (0 <= source < len(nodes) and 0 <= sink < len(nodes)):
        raise ValueError('endpoint outside graph')
    if suffix_lower_bound is not None and len(suffix_lower_bound) != len(nodes):
        raise ValueError('suffix dimensions differ')
    # -1 denotes no released owner; actual owner IDs must be nonnegative.
    if target_owner < 0 or any(n < 0 for members in owners for n in members):
        raise ValueError('owner IDs must be nonnegative')
    members = [set(values) - {target_owner} for values in owners]
    if any(c < 0 for c in capacities):
        raise ValueError('negative capacity')
    if len(members[source]) >= capacities[source]:
        raise ValueError('source must already be admissible')
    start = (source, -1)
    distances = {start: 0}
    parents = {}
    serial = count()
    pending = [(0, next(serial), start)]
    expanded = 0
    while pending:
        value, _, state = heappop(pending)
        if value != distances[state]:
            continue
        expanded += 1
        u, released = state
        if u == sink:
            path = []
            cursor = state
            while cursor != start:
                previous, edge_index = parents[cursor]
                path.append((cursor[0], edge_index))
                cursor = previous
            path.reverse()
            return dict(found=True, delay=value, released_owner=None if released == -1 else released,
                        path_nodes=[source] + [v for v, _ in path],
                        path_edges=[index for _, index in path], expanded=expanded,
                        discovered_states=len(distances))
        begin, size, *_ = nodes[u]
        for index in range(begin, begin + size):
            v, _, delay = edges[index]
            if delay < 0:
                raise ValueError('negative edge delay')
            candidate = value + delay
            if candidate > maximum_delay:
                continue
            if suffix_lower_bound is not None and candidate + suffix_lower_bound[v] > maximum_delay:
                continue
            occupied = members[v]
            used = len(occupied) - (released in occupied)
            choices = [released] if used < capacities[v] else []
            if not choices and released == -1 and len(occupied) == capacities[v] and capacities[v] > 0:
                choices = sorted(occupied)
            for owner in choices:
                next_state = (v, owner)
                if candidate < distances.get(next_state, maximum_delay + 1):
                    distances[next_state] = candidate
                    parents[next_state] = (state, index)
                    heappush(pending, (candidate, next(serial), next_state))
    return dict(found=False, expanded=expanded, discovered_states=len(distances))
