"""Small-graph exact additive nonnegative RC/price reference; not a NET tree solver.

Keep nondominated (raw RC, weighted objective) labels at each node. Limits
return UNKNOWN rather than an infeasibility certificate. Buffered arcs must
be converted to exact nonnegative integer increments by the caller.
"""
from heapq import heappush, heappop


def search(adjacency, source, sink, budget, initial_raw=0, max_labels=100000):
    if budget < 0 or initial_raw < 0 or max_labels < 1:
        raise ValueError('invalid budget/initial RC/label cap')
    for arcs in adjacency.values():
        for edge, dest, raw, penalty in arcs:
            if raw < 0 or penalty < 0:
                raise ValueError('negative increment')
    if initial_raw > budget:
        return {'status': 'INFEASIBLE', 'labels': 0}
    labels = {source: [(initial_raw, initial_raw)]}
    queue = [(initial_raw, initial_raw, 0, source, ())]
    serial = 0
    created = 1
    while queue:
        cost, raw, _, node, path = heappop(queue)
        if (raw, cost) not in labels.get(node, []):
            continue
        if node == sink:
            return dict(status='FOUND', raw=raw, cost=cost, edges=list(path), labels=created)
        for edge, dest, increment, penalty in adjacency.get(node, ()):
            nr, nc = raw + increment, cost + increment + penalty
            if nr > budget:
                continue
            frontier = labels.setdefault(dest, [])
            if any(r <= nr and c <= nc for r, c in frontier):
                continue
            if created >= max_labels:
                return {'status': 'UNKNOWN_LABEL_LIMIT', 'labels': created}
            frontier[:] = [(r, c) for r, c in frontier if not (nr <= r and nc <= c)]
            frontier.append((nr, nc))
            serial += 1
            created += 1
            heappush(queue, (nc, nr, serial, dest, path + (edge,)))
    return {'status': 'INFEASIBLE', 'labels': created}
