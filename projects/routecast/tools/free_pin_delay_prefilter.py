"""Exact minimum-delay feasibility for multiple target pins in one traversal.

No cost optimum, path, ownership or native timing certificate is returned.
"""
import heapq
from prepared_budget_pin_candidates import PreparedContext

def feasible_targets(engine, context, source, sink, source_ptc, targets, budget, blocked_edges=()):
    if type(context) is not PreparedContext or context.owner is not engine or engine._contexts.get(id(context)) is not context:
        raise ValueError('foreign prepared context')
    if type(source) is not int or source not in engine.catalog.sources:
        raise ValueError('invalid source')
    if type(sink) is not int or sink not in engine.catalog.sinks:
        raise ValueError('invalid sink')
    if type(source_ptc) is not int or source_ptc not in engine.catalog.sources[source].physical_pins:
        raise ValueError('invalid source pin')
    if type(budget) is not int or budget < 0:
        raise ValueError('invalid budget')
    pool = engine.catalog.sinks[sink].physical_pins
    targets = tuple(targets)
    if any(type(p) is not int or p not in pool for p in targets):
        raise ValueError('invalid target pin')
    targets = frozenset(targets)
    forbidden = frozenset(blocked_edges)
    if any(type(e) is not int or not 0 <= e < len(engine.graph.edges) for e in forbidden):
        raise ValueError('invalid blocked edge')
    opins = frozenset(engine.catalog.sources[source].physical_pins[source_ptc])
    terminal_pins = {node: p for p in targets for node in pool[p]}
    lower = {source: 0}
    queue = [(0, source)]
    settled = set()
    delays = {}
    examined = 0
    while queue:
        value, node = heapq.heappop(queue)
        if node in settled or lower[node] != value:
            continue
        settled.add(node)
        for eid in engine.outgoing[node]:
            examined += 1
            if eid in forbidden:
                continue
            edge = engine.graph.edges[eid]
            dest = edge.sink
            if engine.graph.nodes[dest].capacity <= 0 or dest in context.blocked:
                continue
            candidate = value + context.delays[eid]
            if candidate > budget:
                continue
            if node in terminal_pins:
                if dest == sink:
                    ptc = terminal_pins[node]
                    delays[ptc] = min(delays.get(ptc, candidate), candidate)
                continue
            if node == source:
                if dest not in opins:
                    continue
            elif dest not in engine.channels and dest not in terminal_pins:
                continue
            if dest not in lower or candidate < lower[dest]:
                lower[dest] = candidate
                heapq.heappush(queue, (candidate, dest))
    return {'feasible_targets': sorted(delays), 'minimum_delays': delays,
            'settled_nodes': len(settled), 'examined_edges': examined,
            'scope': 'Exact additive-delay feasibility only; no label cap and no cost or commit certificate'}
