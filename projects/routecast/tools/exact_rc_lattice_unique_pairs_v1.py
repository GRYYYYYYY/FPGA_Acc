"""Exact RC lattice: repeated electrical classes do not change an LCM."""
from math import lcm
from buffered_rc_node_classes import arc_delay

def exact_scale(ids, classes, switches, edges):
    scale = 1
    for class_id in set(ids):
        resistance, capacitance = classes[class_id]
        scale = lcm(scale, (resistance * capacitance / 2).denominator)
    pairs = {(ids[edges[eid].sink], edges[eid].switch_id)
             for eid in range(len(edges))}
    for class_id, switch_id in pairs:
        scale = lcm(scale, arc_delay(classes, switches, class_id, switch_id).denominator)
    return scale, len(pairs)
