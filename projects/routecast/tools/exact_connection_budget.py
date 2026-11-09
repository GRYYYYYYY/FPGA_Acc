"""Exact single-connection cap in fixed max-plus DAG, including repeated uses."""
from fractions import Fraction as F


def connection_cap(dag, connection_id, target_ns):
    cid = str(connection_id)
    if cid not in dag.budgets or isinstance(target_ns, (bool, float)):
        raise ValueError('known connection and exact target required')
    target = F(target_ns)
    if target < 0:
        raise ValueError('negative target')
    # Every path delay is b + k*x. Retain maximal b for each count k.
    envelopes = {}
    for node in dag.order:
        terms = {0: F(0)}  # Matches DAG zero-arrival clamp at every node.
        for source, offset, edge_cid in dag.incoming[node]:
            repeat = int(edge_cid == cid)
            fixed = offset + (dag.budgets[edge_cid] if edge_cid is not None and not repeat else 0)
            for count, base in envelopes[source].items():
                k = count + repeat
                value = base + fixed
                if k not in terms or value > terms[k]:
                    terms[k] = value
        envelopes[node] = terms
    caps = []
    coefficients = {}
    for node in dag.sinks:
        for count, base in envelopes[node].items():
            coefficients[count] = max(coefficients.get(count, base), base)
            if base > target:
                return dict(feasible=False, cap_ns=None, reason='ZERO_DELAY_STILL_EXCEEDS_TARGET')
            if count:
                caps.append((target-base)/count)
    return dict(feasible=True, cap_ns=min(caps) if caps else None,
                reason='BOUNDED' if caps else 'NO_SINK_DEPENDENCY',
                maximum_repetitions=max(coefficients))
