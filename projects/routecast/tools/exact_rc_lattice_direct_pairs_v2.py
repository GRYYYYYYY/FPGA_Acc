"""Full independent RC lattice scan without per-edge namespace construction.

Only original CompactEdges with read-only packed arrays use the direct path.
No scale/pair result is cached and no edge is omitted. Other edge APIs retain
exactly the original implementation.
"""
from math import lcm
from immutable_xml_prediction_audit import CompactEdges
from buffered_rc_node_classes import arc_delay
from exact_rc_lattice_unique_pairs_v1 import exact_scale as original


def exact_scale(ids, classes, switches, edges):
    if type(edges) is not CompactEdges:
        return original(ids, classes, switches, edges)
    destination, switch = edges.destination, edges.switch
    for values in (edges.source, destination, switch):
        if not isinstance(values, memoryview) or not values.readonly or values.ndim != 1 or values.format != 'Q':
            raise ValueError('original read-only packed edge arrays required')
        if len(values) != len(edges):
            raise ValueError('edge array lengths differ')
    scale = 1
    for class_id in set(ids):
        resistance, capacitance = classes[class_id]
        scale = lcm(scale, (resistance * capacitance / 2).denominator)
    pairs = {(ids[node], switch_id) for node, switch_id in zip(destination, switch)}
    for class_id, switch_id in pairs:
        scale = lcm(scale, arc_delay(classes, switches, class_id, switch_id).denominator)
    return scale, len(pairs)
