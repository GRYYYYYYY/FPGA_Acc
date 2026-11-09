"""Compare optimal objective and atomic/shared-tree semantics, not tie-path parity."""
import json
import random
import resource
from collections import Counter
from fractions import Fraction
from pathlib import Path

from archive_design_exposure_v3 import sha
from criticality_shared_tree_sparse_reference_v3 import Graph as Reference
from static_quotient_lower_bound_v1 import LowerBound, Snapshot, Graph


def main():
    resource.setrlimit(resource.RLIMIT_AS, (256*2**20, 256*2**20))
    cases = consistency = evictions = 0
    maximum_bits = 0
    statuses = Counter()
    for seed in range(200):
        rng = random.Random(seed)
        n = rng.randrange(4, 34)
        offsets, dest, inc = [0], [], []
        for u in range(n):
            for v in range(n):
                if rng.random() < .14:
                    dest.append(v)
                    inc.append(rng.randrange(7)+(2**110 if seed%2 and rng.random()<.3 else 0))
            offsets.append(len(dest))
        f = dict(row_offsets=offsets, dest_ranks=dest)
        initial = [rng.randrange(4) for _ in range(n)]
        floor = [rng.randrange(10)+(2**121 if seed%3==0 else 0) for _ in range(n)]
        group_count = rng.randrange(2, n+1)
        groups = list(range(group_count))+[rng.randrange(group_count) for _ in range(n-group_count)]
        lower = LowerBound(f, inc, initial, floor, groups, max_targets=2)
        candidate, reference = Graph(lower), Reference(f, inc, initial)
        for _ in range(4):
            source = rng.randrange(n)
            tree = candidate.tree(source)
            for step in range(6):
                target = rng.randrange(n)
                criticality = [Fraction(0), Fraction(1), Fraction(2, 3), Fraction(2**62-11, 2**63-25)][step%4]
                prices = [v+rng.randrange(20)+(2**126 if seed%4==0 else 0) for v in floor]
                snapshot = Snapshot(lower, prices)
                h = lower.heuristic(target, criticality)
                assert h[target] == 0
                p, q = criticality.numerator, criticality.denominator
                for u in range(n):
                    for slot in range(offsets[u], offsets[u+1]):
                        v = dest[slot]
                        if h[v] is not None:
                            assert h[u] is not None
                            assert h[u] <= p*inc[slot]+(q-p)*prices[v]+h[v]
                        consistency += 1
                oracle = reference.tree(source)
                oracle.arrival, oracle.parents = dict(tree.arrival), dict(tree.parents)
                expected = oracle.expand(target, criticality, snapshot, 2**256)
                before = dict(tree.arrival), dict(tree.parents)
                budget = rng.randrange(10) if step%3 == 0 else 2**256
                actual = tree.expand(target, criticality, snapshot, budget)
                assert (actual['status']=='UNREACHABLE') == (expected['status']=='UNREACHABLE')
                if expected['status'] != 'UNREACHABLE':
                    assert actual['objective_numerator'] == expected['objective_numerator']
                    assert actual['objective_denominator'] == expected['objective_denominator']
                    maximum_bits = max(maximum_bits, actual['objective_numerator'].bit_length())
                    u, raw, visited = source, initial[source], {source}
                    for slot in actual['path_slots']:
                        assert offsets[u] <= slot < offsets[u+1]
                        u = dest[slot]
                        assert u not in visited
                        visited.add(u)
                        raw += inc[slot]
                    assert u == target and raw == actual['raw']
                    assert actual['committed'] == (raw <= budget)
                if not actual['committed']:
                    assert before == (tree.arrival, tree.parents)
                else:
                    assert all(tree.arrival[u] == value for u, value in before[0].items())
                    assert all(tree.parents[u] == value for u, value in before[1].items())
                statuses[actual['status']] += 1
                cases += 1
        evictions += lower.evictions
        assert len(lower.cache) <= 2
    # Two equal weighted-cost paths have different raw costs: explicitly preserve
    # this limitation rather than claim equal raw-budget status/path tie policy.
    f = dict(row_offsets=[0, 2, 3, 4, 4], dest_ranks=[1, 2, 3, 3])
    lower = LowerBound(f, [1, 5, 1, 5], [0]*4, [0]*4, list(range(4)))
    snapshot = Snapshot(lower, [0, 0, 0, 0])
    x = Graph(lower).tree(0).expand(3, Fraction(0), snapshot, 3)
    assert x['objective_numerator'] == 0
    rejected = 0
    for values in ([0, -1, 0, 0], [True, 0, 0, 0], [0, 0]):
        try:
            Snapshot(lower, values)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError('invalid snapshot accepted')
    positive = LowerBound(f, [1, 5, 1, 5], [0]*4, [1]*4, list(range(4)))
    try:
        Snapshot(positive, [0]*4)
    except ValueError:
        rejected += 1
    else:
        raise AssertionError('below-floor snapshot accepted')
    assert cases == 4800 and maximum_bits > 160 and evictions > 0
    assert all(statuses[k] for k in ('COMMITTED', 'UNREACHABLE', 'RETAIN_RAW_BUDGET'))
    root = Path(__file__).resolve().parents[1]
    out = root/'experiments/static_quotient_lower_bound_contract_v1_2026-10-17'
    out.mkdir()
    result = dict(bindings={str(p):sha(p) for p in (Path(__file__),root/'tools/static_quotient_lower_bound_v1.py',
                   root/'tools/criticality_shared_tree_sparse_reference_v3.py')},
                  all_pass=True, random_graphs=200, shared_tree_expansions=cases,
                  original_arc_consistency_checks=consistency, status_counts=dict(statuses),
                  cache_evictions=evictions, invalid_snapshot_rejections=rejected,
                  maximum_weighted_objective_bits=maximum_bits,
                  all_objectives_equal_independent_Dijkstra=True,
                  paths_raw_reconstruction_retained_seeds_and_atomic_rejection_pass=True,
                  tie_path_parity_claimed=False, raw_budget_status_parity_claimed=False,
                  scope='Exact arbitrary-integer primitive only. Weighted optimal cost preserved; changed A* visitation may select different equal-score raw paths, hence budget status and complete model trajectories are not claimed equal. No native labels, complete model/quality, measured runtime gain, hardware or workflow claim.')
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))


if __name__ == '__main__':
    main()
