"""Direct exact RC/base preparation with integer cost-class keys.

Avoids intermediate length-switch/base-only arc copies. Preserves the prior
supported configurable buffered graph domain and exact cost objective.
"""
from fractions import Fraction
import xml.etree.ElementTree as ET
from bound_indexed_cost import validate_binding
from compact_indexed_sketch import CompactIndexedSketch
from path_rc import PathRC, State


class DirectBoundRCBase(CompactIndexedSketch):
    def __init__(self, graph, text, bindings_csv, identity, scale=10**6):
        if type(scale) is not int or scale < 1:
            raise ValueError('invalid scale')
        norm, rows, indices, expected = validate_binding(graph, text, bindings_csv, identity)
        rc = PathRC(graph)
        if any(not fields[0] for fields in rc.switches.values()):
            raise ValueError('nonbuffered graph requires resistance state')
        if any(ET.fromstring(xml).get('type') in ('short', 'buffer') for xml in graph.switches.values()):
            raise ValueError('non-configurable switch closure is not implemented')
        self.graph = graph
        self.mode = 'rr_length_switch'  # Preserve authenticated transport context.
        self.node_budget = len(graph.nodes)
        self.scale = scale
        self.normalization = Fraction(norm)
        self.identity = expected
        resistance_ids = {}
        rc_ids = {}
        source_classes = {}
        sink_classes = {}
        for n, fields in rc.nodes.items():
            source_classes[n] = resistance_ids.setdefault(fields[0], len(resistance_ids))
            sink_classes[n] = rc_ids.setdefault(fields, len(rc_ids))
        bases = {i: Fraction(row['base']) for i, row in rows.items()}
        outgoing = {n: [] for n in graph.nodes}
        cache = {}
        for eid, edge in enumerate(graph.edges):
            key = (source_classes[edge.source], sink_classes[edge.sink],
                   edge.switch_id, indices[edge.sink])
            if key not in cache:
                delay = rc.step(State(Fraction(0), Fraction(0)), eid).delay
                if delay < 0:
                    raise ValueError('negative RC increment')
                cache[key] = round((delay + bases[key[3]]) / self.normalization * scale / 2)
            weight = cache[key] if graph.nodes[edge.sink].capacity > 0 else None
            outgoing[edge.source].append((eid, edge.sink, weight))
        self.outgoing = {n: tuple(arcs) for n, arcs in outgoing.items()}
        self.cost_classes = len(cache)
