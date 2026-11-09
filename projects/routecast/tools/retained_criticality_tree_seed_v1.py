"""Atomic import of validated additive-RC paths into an empty reference tree."""
def seed(tree, paths):
    if tree.parents or tree.arrival != {tree.source: tree.initial[tree.source]}:
        raise ValueError('requires empty source tree')
    arrival = dict(tree.arrival)
    parents = {}
    for target, slots, raw_budget in paths:
        if type(target) is not int or not 0 <= target < tree.n:
            raise ValueError('target')
        if type(raw_budget) is not int or raw_budget < 0:
            raise ValueError('budget')
        u = tree.source
        visited = {u}
        for slot in slots:
            if type(slot) is not int or not tree.offsets[u] <= slot < tree.offsets[u + 1]:
                raise ValueError('edge source/domain')
            v = tree.dest[slot]
            if v in visited:
                raise ValueError('cyclic path')
            visited.add(v)
            parent = (u, slot)
            value = arrival[u] + tree.inc[slot]
            if v in parents and parents[v] != parent:
                raise ValueError('shared parent conflict')
            if v in arrival and arrival[v] != value:
                raise ValueError('shared arrival conflict')
            parents[v] = parent
            arrival[v] = value
            u = v
        if u != target or arrival[u] > raw_budget:
            raise ValueError('endpoint/raw budget')
    tree.parents = parents
    tree.arrival = arrival
    return frozenset(arrival)
