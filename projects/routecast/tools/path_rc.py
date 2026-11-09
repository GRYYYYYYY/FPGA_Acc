"""Exact-decimal oracle for VPR connection expansion RC, not route-tree STA.

Uses serialized decimal values and Fraction arithmetic, not native float parity.
Caller supplies tree-start delay/resistance. No branching load, Cin/Cout addition,
lookahead, congestion or criticality is inferred. Signed Cinternal correction is
preserved; this module makes no nonnegative edge-cost/Dijkstra assumption.
"""
from dataclasses import dataclass
from fractions import Fraction
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
import xml.etree.ElementTree as ET


def number(value):
    if isinstance(value, bool):
        raise ValueError('boolean timing value')
    if isinstance(value, Fraction):
        result = value
    else:
        try:
            decimal = Decimal(str(value))
            if not decimal.is_finite():
                raise ValueError('nonfinite timing value')
            result = Fraction(decimal)
        except (InvalidOperation, TypeError) as exc:
            raise ValueError('invalid timing value') from exc
    if result < 0:
        raise ValueError('negative physical timing value')
    return result


@dataclass(frozen=True)
class State:
    resistance: Fraction
    delay: Fraction


class PathRC:
    def __init__(self, graph):
        self.graph = graph
        nodes = {}
        for nid, node in graph.nodes.items():
            t = dict(node.timing)
            # Node RC must be present: missing values are not assumed zero.
            if 'R' not in t or 'C' not in t:
                raise ValueError('missing node RC')
            nodes[nid] = (number(t['R']), number(t['C']))
        switches = {}
        for sid, xml in graph.switches.items():
            root = ET.fromstring(xml)
            kind = root.attrib.get('type')
            if kind not in {'mux', 'tristate', 'buffer', 'pass_gate', 'short'}:
                raise ValueError('unsupported switch type')
            t = root.find('timing')
            if t is None:
                raise ValueError('missing switch timing element')
            # Native RR reader initializes omitted switch timing fields to zero.
            switches[sid] = (kind in {'mux', 'tristate', 'buffer'},
                             number(t.get('R', '0')), number(t.get('Tdel', '0')),
                             number(t.get('Cinternal', '0')))
        self.nodes = MappingProxyType(nodes)
        self.switches = MappingProxyType(switches)

    def step(self, state, edge_id):
        if type(edge_id) is not int or not 0 <= edge_id < len(self.graph.edges):
            raise ValueError('invalid edge id')
        upstream = number(state.resistance)
        if not isinstance(state.delay, Fraction):
            raise ValueError('delay must be exact Fraction (may be signed)')
        edge = self.graph.edges[edge_id]
        buffered, sr, intrinsic, internal = self.switches[edge.switch_id]
        r, c = self.nodes[edge.sink]
        from_r, _ = self.nodes[edge.source]
        new_r = (Fraction(0) if buffered else upstream) + sr + r
        increment = intrinsic + (new_r-r/2)*c + (new_r-from_r/2)*internal
        return State(new_r, state.delay+increment)

    def path(self, source, edge_ids, initial_resistance=0, initial_delay=0):
        if source not in self.nodes:
            raise ValueError('unknown source')
        state = State(number(initial_resistance), number(initial_delay))
        current = source
        visited = {source}
        for eid in edge_ids:
            if type(eid) is not int or not 0 <= eid < len(self.graph.edges):
                raise ValueError('invalid edge id')
            edge = self.graph.edges[eid]
            if edge.source != current or edge.sink in visited:
                raise ValueError('discontinuous or cyclic path')
            state = self.step(state, eid)
            current = edge.sink
            visited.add(current)
        return state
