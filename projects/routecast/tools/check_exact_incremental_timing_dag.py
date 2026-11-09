"""Independent full recurrence versus sparse transactions, synthetic and real."""
import json
import random
from fractions import Fraction as F
from pathlib import Path
from exact_incremental_timing_dag import ExactTimingDAG

ROOT = Path(__file__).resolve().parents[1]

def full(nodes, edges, sinks, budgets):
    arrival = dict.fromkeys(nodes, F(0))
    # Repeated relaxation is independent of the evaluator's topology cache.
    for _ in nodes:
        changed = False
        for u, v, offset, c in edges:
            value = arrival[u] + offset + (budgets[c] if c is not None else 0)
            if value > arrival[v]:
                arrival[v] = value
                changed = True
        if not changed:
            break
    return max(arrival[n] for n in sinks), arrival

rng = random.Random(6129)
checks = 0
for _ in range(50):
    nodes = list(range(25))
    budgets = {str(c): F(rng.randrange(10), 7) for c in range(8)}
    edges = [(u, v, F(rng.randrange(10), 13), str(rng.randrange(8)) if rng.random() < .7 else None)
             for v in nodes for u in range(v) if rng.random() < .12]
    rng.shuffle(edges)
    dag = ExactTimingDAG(nodes, edges, nodes[-4:], budgets)
    assert (dag.cpd, dag.arrivals) == full(nodes, edges, nodes[-4:], budgets)
    for trial in range(40):
        changes = {str(rng.randrange(8)): F(rng.randrange(20), 17) for _ in range(3)}
        before = dict(dag.arrivals), dict(dag.budgets)
        expected_budgets = dict(budgets, **changes)
        expected, arrivals = full(nodes, edges, nodes[-4:], expected_budgets)
        assert dag.update(changes) == expected
        assert (dag.arrivals, dag.budgets) == before
        if trial % 3 == 0:
            assert dag.update(changes, commit=True) == expected
            budgets = expected_budgets
            assert dag.arrivals == arrivals and dag.budgets == budgets
        checks += 1
    before = dict(dag.arrivals), dict(dag.budgets)
    try:
        dag.update({'0': F(3), 'missing': F(1)}, commit=True)
    except ValueError:
        pass
    else:
        raise AssertionError('invalid update accepted')
    assert (dag.arrivals, dag.budgets) == before
    # A failure after mutation must also roll back, even when commit requested.
    original = dag._arrival
    def failing(n):
        raise RuntimeError('injected evaluation failure')
    dag._arrival = failing
    if dag.targets['0']:
        try:
            dag.update({'0': dag.budgets['0'] + 1}, commit=True)
        except RuntimeError:
            pass
        else:
            raise AssertionError('failure injection did not run')
        assert (dag.arrivals, dag.budgets) == before
    dag._arrival = original

real_checks = 0
for w, i in [(8, 0), (8, 2), (16, 0), (32, 2)]:
    def load(rel):
        return json.loads((ROOT / 'experiments' / rel).read_text())
    graph = load(f'mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json')
    mapping = load(f'mux_full_timing_rr_2026-10-06/w{w}.json')
    metadata = load(f'mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json')
    frozen = load(f'mux_net_slack_budgets_2026-10-06/w{w}_m{i}.json')
    dag = ExactTimingDAG.from_native_metadata(graph, mapping, metadata, frozen['initial_budgets_ns'])
    for row in frozen['trace']:
        cids = list(map(str, row['connection_ids']))
        before = dict(dag.budgets), dict(dag.arrivals)
        assert dag.update({c: F(1) for c in cids}) == F(row['cap_cpd_ns'])
        assert (dag.budgets, dag.arrivals) == before
        changes = {c: dag.budgets[c] + F(row['alpha']) * (1 - dag.budgets[c]) for c in cids}
        assert dag.update(changes, commit=True) == F(row['budget_cpd_ns'])
        real_checks += 1
    assert dag.budgets == {c: F(v) for c, v in frozen['budgets_ns'].items()}
    assert dag.cpd == F(frozen['model_budget_cpd_ns'])
print(json.dumps({'synthetic_transactions': checks, 'real_trace_steps': real_checks,
                  'real_cases': 4, 'status': 'PASS'}))
