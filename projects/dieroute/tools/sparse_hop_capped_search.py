"""Minimize hops under hard additive-delay and crossing budgets."""
from heapq import heappop, heappush


def search(adjacency, allowed, source, sink, fixed_parent, crossing_budget,
           maximum_labels=262144, delay_budget=None):
    if crossing_budget < 0 or maximum_labels < 1 or delay_budget is None or delay_budget < 0:
        raise ValueError('Finite nonnegative delay and crossing budgets required')
    if not allowed(source) or not allowed(sink):
        return {'status': 'no_feasible_path', 'labels': 0, 'expanded': 0}
    labels = [(source, 0, 0, 0, -1)]
    frontier = {source: [0]}
    active = {0}
    queue = [(0, 0, 0, 0)]
    expanded = 0
    while queue:
        hops, delay, used, index = heappop(queue)
        if index not in active:
            continue
        u = labels[index][0]
        expanded += 1
        if u == sink:
            path = []
            cursor = index
            while cursor != -1:
                path.append(labels[cursor][0])
                cursor = labels[cursor][4]
            path.reverse()
            assert len(path) == len(set(path))
            return {'status': 'optimal_bounded_delay_path', 'objective': 'hops_delay_crossings',
                    'delay': delay, 'hops': hops, 'crossings': used,
                    'path_nodes': path, 'labels': len(labels), 'expanded': expanded}
        for v, weight, charge in adjacency(u):
            if weight < 0 or charge < 0:
                raise ValueError('Negative edge cost')
            cost = (used + charge, delay + weight, hops + 1)
            if cost[0] > crossing_budget or cost[1] > delay_budget or v == source or not allowed(v):
                continue
            if v in fixed_parent and fixed_parent[v] != u:
                continue
            old = frontier.get(v, [])
            if any(all(a <= b for a, b in zip(labels[j][1:4], cost)) for j in old):
                continue
            if len(labels) >= maximum_labels:
                return {'status': 'label_budget_exhausted', 'labels': len(labels), 'expanded': expanded}
            keep = []
            for j in old:
                if all(a <= b for a, b in zip(cost, labels[j][1:4])):
                    active.discard(j)
                else:
                    keep.append(j)
            k = len(labels)
            labels.append((v, *cost, index))
            active.add(k)
            frontier[v] = keep + [k]
            heappush(queue, (cost[2], cost[1], cost[0], k))
    return {'status': 'no_feasible_path', 'labels': len(labels), 'expanded': expanded}
