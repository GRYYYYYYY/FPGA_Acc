"""Cross-capacity exact search/retained parity through actual eviction paths."""
import ast
import json
import random
import resource
import sys
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path

from compiled_quotient_model_factory_v1 import create as original
from compiled_quotient_model_factory_v2 import create, CACHE_ENTRIES, BINARY
from static_quotient_lower_bound_v1 import Snapshot

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha


def main():
    resource.setrlimit(resource.RLIMIT_AS, (2**30, 2**30))
    n = 600
    nodes = []
    offsets, dest, inc = [0], [], []
    for u in range(n):
        node = ET.Element('node', type='CHANX', direction='INC_DIR')
        ET.SubElement(node, 'loc', layer='0', xlow=str(4*u), xhigh=str(4*u+1), ylow='0', yhigh='0')
        ET.SubElement(node, 'segment', segment_id='0')
        nodes.append(node)
        for delta in (1, 17):
            dest.append((u+delta)%n)
            inc.append(2**112+u+delta)
        offsets.append(len(dest))
    fields = dict(row_offsets=offsets, dest_ranks=dest, capacities=[1]*n)
    base = [2**100+u for u in range(n)]
    a, b = original(fields, inc, [0]*n, nodes, base, 3), create(fields, inc, [0]*n, nodes, base, 3)
    assert a.lower.groups == b.lower.groups and a.lower.floor == b.lower.floor
    assert a.lower.reverse == b.lower.reverse and CACHE_ENTRIES == b.lower.max_targets == 512
    rng = random.Random(20261017)
    calls = maximum = 0
    try:
        sequence = list(range(n))+list(range(64, 576))+[rng.randrange(n) for _ in range(400)]
        for i, target in enumerate(sequence):
            source = i%n
            x, y = a.tree(source), b.tree(source)
            prices = [v+i%7 for v in a.lower.floor]
            crit = Fraction(2**62-11, 2**63-25)
            budget = 2**127 if i%4 else 0
            left = x.expand(target, crit, Snapshot(a.lower, prices), budget)
            right = y.expand(target, crit, Snapshot(b.lower, prices), budget)
            assert left == right and x.parents == y.parents and x.arrival == y.arrival
            assert a.last_stats == b.last_stats
            maximum = max(maximum, right.get('objective_numerator', 0).bit_length())
            # Continue a valid retained tree after a different target/table lookup.
            target = (target+13)%n
            left = x.expand(target, crit, Snapshot(a.lower, prices), 2**127)
            right = y.expand(target, crit, Snapshot(b.lower, prices), 2**127)
            assert left == right and x.parents == y.parents and x.arrival == y.arrival
            assert a.last_stats == b.last_stats
            calls += 2
        assert a.lower.evictions > 0 and b.lower.evictions > 0 and maximum > 160
        report = b.cache_report()
        assert report['table_calls'] == calls
        assert report['native_conversions'] >= report['reverse_table_builds'] > 512
        assert report['native_array_allocated_bytes'] >= 72*n*512
        assert report['lower_tuple_container_bytes'] >= 16*n*512
    finally:
        a.close()
        b.close()
    old = R/'tools/run_design_scoped_quotient_astar_retained_tree_v1.py'
    new = R/'tools/run_design_scoped_quotient_astar_retained_tree_v2.py'
    # Prove the full driver differs only in the intended factory import,
    # explicit policy metadata, and one cost-report serialization statement.
    text = new.read_text().replace('from compiled_quotient_model_factory_v2 import', 'from compiled_quotient_model_factory_v1 import').replace('targetLRU512;', 'targetLRU64;')
    added = " (out/'quotient_cache_cost.json').write_text(json.dumps(criticality_graph.cache_report(),indent=2)+'\\n')\n"
    assert text.count(added) == 1
    text = text.replace(added, '')
    assert ast.dump(ast.parse(text)) == ast.dump(ast.parse(old.read_text()))
    bindings = closure([Path(__file__), new])
    bindings[str(BINARY)] = sha(BINARY)
    out = R/'experiments/quotient_cache512_factory_contract_v2_2026-10-17'
    out.mkdir()
    result = dict(all_pass=True, bindings=bindings, groups=n, sequential_and_retained_queries=calls,
        maximum_objective_bits=maximum, original_capacity=64, candidate_capacity=512,
        both_capacities_exercised_evictions=True, exact_result_path_tree_work_parity=True,
        full_driver_AST_equal_except_cache_factory_policy_and_cost_report=True,
        cost_report=report, whole_neuron_or_workflow_gain_proven=False, promoted=False)
    (out/'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'bindings'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
