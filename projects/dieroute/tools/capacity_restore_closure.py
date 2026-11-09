"""Compute a sufficient whole-net restoration closure using actual node capacities.

This algorithm guarantees capacity for valid input allocations, not native routing
legality or quality. It can restore more nets than a minimum solution.
"""
from collections import defaultdict


def restore_closure(baseline, candidate, capacities, seeds):
    """Return restored net IDs and conflict counts for each monotone wave.

    Allocations map net IDs to sets of occupied RR nodes, including roots.
    Capacity counts nets, so shared branches within a net count once.
    Both complete input allocations must already satisfy capacity.
    """
    if set(baseline) != set(candidate):
        raise ValueError('Baseline and candidate must contain identical net IDs')
    baseline = {n: frozenset(nodes) for n, nodes in baseline.items()}
    candidate = {n: frozenset(nodes) for n, nodes in candidate.items()}
    restored = set(seeds)
    if not restored <= baseline.keys():
        raise ValueError('Unknown seed net')
    for mapping in [baseline, candidate]:
        used = defaultdict(int)
        for nodes in mapping.values():
            for node in nodes:
                if node not in capacities or capacities[node] < 0:
                    raise ValueError('Missing or negative node capacity')
                used[node] += 1
        if any(count > capacities[node] for node, count in used.items()):
            raise ValueError('Input allocation exceeds capacity')
    waves = []
    while True:
        owners = defaultdict(set)
        for net in baseline:
            for node in baseline[net] if net in restored else candidate[net]:
                owners[node].add(net)
        conflicts = {node: nets for node, nets in owners.items()
                     if len(nets) > capacities[node]}
        waves.append(dict(restored_nets=len(restored),
                          overused_resources=len(conflicts)))
        if not conflicts:
            return restored, waves
        added = set().union(*conflicts.values()) - restored
        # With a capacity-legal baseline every conflict has an unrestored owner.
        if not added:
            raise RuntimeError('Capacity closure cannot advance')
        restored.update(added)
