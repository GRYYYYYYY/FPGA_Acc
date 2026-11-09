"""Independent original-XML/Fraction reconstruction of the soft budget policy."""
from copy import deepcopy
from independent_fraction_arc_context_v2 import arc_delay


def reconstruct(xml, ids, classes, switches, scale, original):
    positive = {n for n, row in xml.graph.nodes.items() if row.capacity > 0}
    edges = xml.graph.edges
    pairs = {(ids[v], sw) for u, v, sw in zip(edges.source, edges.destination, edges.switch)
             if u in positive and v in positive}
    increments = [arc_delay(classes, switches, cls, sw) * scale for cls, sw in pairs]
    if not increments or any(x.denominator != 1 or x < 0 for x in increments):
        raise ValueError('invalid XML additive lattice')
    maximum = max(x.numerator for x in increments)
    result = deepcopy(original)
    result['original_budget_policy'] = result['budget_policy']
    result['budget_policy'] = 'SOFT_CRITICALITY_SIMPLE_PATH_CAP_V1'
    for row in result['records']:
        a, b = classes[ids[row['source']]]
        initial = a * b * scale / 2
        if initial.denominator != 1 or initial < 0:
            raise ValueError('initial lattice')
        ceiling = initial.numerator + (len(positive)-1) * maximum
        if not 0 <= ceiling < 2**64:
            raise ValueError('uint64 ceiling')
        row['original_budget_integer'] = row['budget_integer']
        row['budget_integer'] = ceiling
        if 'proxy_budget_integer' in row:
            row['original_proxy_budget_integer'] = row['proxy_budget_integer']
            row['proxy_budget_integer'] = ceiling
    return result, maximum
