"""Serial staged uniqueNET replacement with local overflow accounting."""
from collections import Counter


def replace_net(current, old_nodes, new_nodes, capacities, current_overflow):
    old, new = frozenset(old_nodes), frozenset(new_nodes)
    if type(current_overflow) is not int or current_overflow < 0:
        raise ValueError('nonnegative authenticated overflow total required')
    dirty = old ^ new
    if any(type(n) is not int or not 0 <= n < len(capacities) for n in old | new):
        raise ValueError('invalid node identity')
    if any(type(current.get(n, 0)) is not int or current.get(n, 0) < 1 for n in old):
        raise ValueError('old NET contribution absent')
    staged = Counter(current)
    total = current_overflow
    for n in dirty:
        before = current.get(n, 0)
        capacity = capacities[n]
        if type(before) is not int or before < 0 or type(capacity) is not int or capacity < 0:
            raise ValueError('invalid occupancy/capacity')
        after = before + (n in new) - (n in old)
        total += max(0, after-capacity)-max(0, before-capacity)
        if after:
            staged[n] = after
        else:
            staged.pop(n, None)
    if total < 0:
        raise ValueError('inconsistent prior overflow')
    return staged, total, dirty
