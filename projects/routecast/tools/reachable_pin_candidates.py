"""Exhaustive directed reachability with concrete pins; ignores congestion/timing."""
from collections import deque
from pin_choice_catalog import PinChoiceCatalog

class ReachablePins:
    def __init__(self, graph):
        self.graph = graph
        self.catalog = PinChoiceCatalog(graph)
        self.outgoing = {n: [] for n in graph.nodes}
        for eid, edge in enumerate(graph.edges):
            self.outgoing[edge.source].append(eid)

    def query(self, source, sink, source_ptc):
        if type(source) is not int or source not in self.catalog.sources:
            raise ValueError('invalid SOURCE')
        if type(sink) is not int or sink not in self.catalog.sinks:
            raise ValueError('invalid SINK')
        if type(source_ptc) is not int or source_ptc not in self.catalog.sources[source].physical_pins:
            raise ValueError('invalid source physical pin')
        allowed_opins = set(self.catalog.sources[source].physical_pins[source_ptc])
        targets = {rr: ptc for ptc, facets in self.catalog.sinks[sink].physical_pins.items() for rr in facets}
        parent = {source: None}
        queue = deque([source])
        found = {}
        examined = 0
        while queue:
            node = queue.popleft()
            for eid in self.outgoing[node]:
                examined += 1
                edge = self.graph.edges[eid]
                dest = edge.sink
                kind = self.graph.nodes[dest].type
                allowed = (dest in allowed_opins if node == source else
                           kind in {'CHANX', 'CHANY'} or dest in targets)
                if not allowed or self.graph.nodes[dest].capacity <= 0 or dest in parent:
                    continue
                parent[dest] = eid
                if dest in targets:
                    ptc = targets[dest]
                    if ptc not in found:
                        terminal = next(e for e in self.outgoing[dest] if self.graph.edges[e].sink == sink)
                        path = [terminal]
                        cursor = dest
                        while cursor != source:
                            previous = parent[cursor]
                            path.append(previous)
                            cursor = self.graph.edges[previous].source
                        path.reverse()
                        witness = self.catalog.witness(source, sink, path)
                        assert witness['selected_opin_ptc'] == source_ptc
                        found[ptc] = path
                else:
                    queue.append(dest)
        return {'paths': found, 'visited_nodes': len(parent), 'examined_edges': examined,
                'scope': 'fixed source physical pin, enabled channels, target IPIN only; no congestion or packed-equivalence legality'}
