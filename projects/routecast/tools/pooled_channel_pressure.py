"""Fixed geometric/segment pool pressure; no native labels or parameter fitting."""
from collections import defaultdict
from fractions import Fraction

KEYS = ('types', 'directions', 'segments', 'xlow', 'xhigh', 'ylow', 'yhigh', 'layer')


def rows(fields, occupancy):
    groups = defaultdict(list)
    for node, cap in enumerate(fields['capacities']):
        if fields['types'][node] in (4, 5) and cap > 0:
            groups[tuple(fields[key][node] for key in KEYS)].append(node)
    result, proofs = {}, []
    for key, nodes in groups.items():
        excess = 0
        capacity = sum(fields['capacities'][node] for node in nodes)
        for node in nodes:
            used = occupancy.get(node, 0)
            if type(used) is not int or used < 0:
                raise ValueError('invalid channel occupancy')
            excess += max(0, used - fields['capacities'][node])
        if excess:
            value = 1 + Fraction(excess, capacity)
            result.update((node, (fields['capacities'][node], value)) for node in nodes)
            proofs.append({'key': key, 'nodes': nodes, 'capacity': capacity, 'excess': excess})
    return result, proofs


def payload(node_count, digest, pressure):
    if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('invalid graph identity')
    return f'ROUTECAST_PRESSURE_V1 {node_count} {digest}\n' + ''.join(
        f'{node} {cap} {float(value):.9g}\n' for node, (cap, value) in sorted(pressure.items()))
