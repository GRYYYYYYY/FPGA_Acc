"""Isolated retention-off semantic/AST contract; full XML fixture still required."""
import ast
import copy
import json
import resource
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from fractions import Fraction
from pathlib import Path

from compiled_quotient_model_factory_v2 import create, BINARY
from criticality_shared_tree_sparse_reference_v3 import Graph as Reference
from criticality_retained_net_primary_v1 import route
from static_quotient_lower_bound_v1 import Snapshot

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure

POLICY = 'fanout>=16; keep old paths with no globally overused node before virtual owner release; no forced timing flags; wholeNET fallback may revise retained paths'
DISABLED = 'disabled; source-only primary seed; no old clean branches imported; wholeNET fallback unchanged'


def main():
    resource.setrlimit(resource.RLIMIT_AS, (512*2**20, 512*2**20))
    cases = queries = positive_controls = maximum_bits = 0
    statuses = Counter()
    for seed in range(210):
        fanout = [1, 2, 15, 16, 17, 32, 64][seed%7]
        n = fanout+3
        unit = 2**110 if seed%3 == 0 else 1
        offsets, dest, inc = [0], [], []
        for u in range(n):
            row = [(1, unit), (2, unit)] if u == 0 else [(v, (1 if u == 1 else 2)*unit) for v in range(3, n)] if u in (1, 2) else []
            for v, raw in row:
                dest.append(v)
                inc.append(raw)
            offsets.append(len(dest))
        fields = dict(row_offsets=offsets, dest_ranks=dest, capacities=[2]*n)
        edge_ids = [1000+3*i for i in range(len(dest))]
        edge_slots = {eid: i for i, eid in enumerate(edge_ids)}
        nodes = []
        for i in range(n):
            node = ET.Element('node', type='SOURCE' if i == 0 else 'SINK' if i >= 3 else 'IPIN')
            ET.SubElement(node, 'loc', layer='0', xlow=str(4*i), xhigh=str(4*i), ylow='0', yhigh='0')
            nodes.append(node)
        native = create(fields, inc, [0]*n, nodes, [0]*n, 1)
        reference = Reference(fields, inc, [0]*n)
        criticality = [Fraction(0), Fraction(1, 4), Fraction(2, 3), Fraction(2**62-11, 2**63-25)][seed%4]
        prices = {i: 0 for i in range(n)}
        prices[1] = 100*unit if seed%2 else 0
        budget = (2 if seed%5 == 0 else 3)*unit
        qs, old, criticalities = [], [], {}
        for cid, target in enumerate(range(3, n)):
            q = dict(connection_id=cid, net_id=7, source=0, sink=target)
            old_path = [edge_ids[0], edge_ids[offsets[1]+cid]]
            qs.append(q)
            old.append(dict(q, budget_integer=budget, answer=dict(physical_edge_ids=old_path)))
            criticalities[cid] = dict(net=7, source_rr=0, target_rr=target,
                criticality_numerator=criticality.numerator, criticality_denominator=criticality.denominator,
                local_sink_pin=fanout-cid)
        ledger = {i: 1 for i in [0, 1, *range(3, n)]}
        unchanged = copy.deepcopy((old, ledger, prices, criticalities))
        snapshot = Snapshot(native.lower, [prices[i] for i in range(n)])
        try:
            actual = route(native, qs, old, criticalities, snapshot, edge_ids, ledger,
                           fields['capacities'], edge_slots, min_fanout=fanout+1)
            assert actual['retained_connection_ids'] == []
            assert all(row['status'] != 'RETAINED_CLEAN_BRANCH' for row in actual['search_results'])
            tree = reference.tree(0)
            ordered = sorted(qs, key=lambda q: (-criticality, criticalities[q['connection_id']]['local_sink_pin'], q['connection_id']))
            expected, paths, parents, settled, failed = [], {}, {}, set(), None
            for q in ordered:
                value = tree.expand(q['sink'], criticality, prices, budget)
                expected.append(dict(connection_id=q['connection_id'], **value))
                if 'path_slots' in value:
                    paths[q['connection_id']] = [edge_ids[s] for s in value['path_slots']]
                    u = 0
                    for slot in value['path_slots']:
                        v = dest[slot]
                        assert v not in parents or parents[v] == (u, slot)
                        parents[v] = u, slot
                        u = v
                    settled.add(q['sink'])
                else:
                    paths[q['connection_id']] = None
                if not value['committed']:
                    failed = q['connection_id']
                    break
            assert actual['search_results'] == expected
            assert actual['search_calls'] == len(expected)
            assert actual['parents'] == parents and actual['settled'] == settled
            assert actual['complete'] == (failed is None)
            assert actual['first_failed_connection_id'] == failed
            assert actual['order'] == [q['connection_id'] for q in ordered]
            assert actual['attempts'] == [dict(connection_id=q['connection_id'], physical_edge_ids=paths.get(q['connection_id'])) for q in qs]
            if actual['complete']:
                assert actual['search_calls'] == fanout
            if fanout >= 16:
                retained = route(reference, qs, old, criticalities, prices, edge_ids, ledger,
                                 fields['capacities'], edge_slots)
                assert retained['retained_connection_ids'] == list(range(fanout)) and retained['search_calls'] == 0
                assert actual['search_calls'] > 0
                positive_controls += 1
            assert (old, ledger, prices, criticalities) == unchanged
            for row in expected:
                statuses[row['status']] += 1
                maximum_bits = max(maximum_bits, row.get('objective_numerator', 0).bit_length())
            cases += 1
            queries += len(expected)
        finally:
            native.close()
    assert cases == 210 and positive_controls == 120 and maximum_bits > 160
    assert statuses['COMMITTED'] and statuses['RETAIN_RAW_BUDGET']
    driver = R/'tools/run_design_scoped_quotient_astar_no_retention_v1.py'
    original = R/'tools/run_design_scoped_quotient_astar_retained_tree_v2.py'
    text = driver.read_text().replace(DISABLED, POLICY)
    change = "slots,min_fanout=len(queries)+1);parents=primary['parents']"
    assert text.count(change) == 1
    text = text.replace(change, "slots);parents=primary['parents']")
    assert ast.dump(ast.parse(text)) == ast.dump(ast.parse(original.read_text()))
    auditor = R/'tools/verify_scaled_present_no_retention_full_schedule_v1.py'
    old_auditor = R/'tools/verify_scaled_present_retained_tree_full_schedule_v1.py'
    text = auditor.read_text().replace(DISABLED, POLICY)
    empty = "  eligible=[]\n  assert event['retained_connection_ids']==sorted(eligible)"
    old = "  eligible=[]\n  if len(old)>=16:\n   for rec in old:\n    nodes=ownership([rec])\n    if all(ledger.get(node,0)<=xml.graph.nodes[node].capacity for node in nodes):eligible.append(rec['connection_id'])\n  assert event['retained_connection_ids']==sorted(eligible)"
    assert text.count(empty) == 1
    assert ast.dump(ast.parse(text.replace(empty, old))) == ast.dump(ast.parse(old_auditor.read_text()))
    # Execute the exact new auditor's retention assertion against corrupt traces.
    assertion = next(n for n in ast.walk(ast.parse(auditor.read_text())) if isinstance(n, ast.Assert)
                     and "event['retained_connection_ids']" in ast.unparse(n.test))
    code = compile(ast.Module(body=[assertion], type_ignores=[]), str(auditor), 'exec')
    exec(code, dict(event=dict(retained_connection_ids=[]), eligible=[]))
    for bad in ([0], [0, 0], [False], ['0']):
        try:
            exec(code, dict(event=dict(retained_connection_ids=bad), eligible=[]))
        except AssertionError:
            pass
        else:
            raise AssertionError('Corrupt retained trace accepted')
    bindings = closure([Path(__file__), driver, auditor])
    bindings[str(BINARY)] = sha(BINARY)
    prereg = R/'experiments/neuron_high_fanout_retention_ablation_prereg_v1_2026-10-17/protocol.json'
    bindings[str(prereg)] = sha(prereg)
    out = R/'experiments/quotient_no_retention_primary_contract_v1_2026-10-17'
    out.mkdir()
    result = dict(all_pass=True, bindings=bindings, NET_cases=cases,
        exact_unseeded_native_vs_independent_reference_queries=queries,
        retained_positive_controls=positive_controls, maximum_objective_bits=maximum_bits,
        status_counts=dict(statuses), raw_budget_rejection_stops_trace=True,
        old_records_prices_ledger_criticalities_unchanged=True,
        producer_AST_unchanged_except_retention_threshold_and_policy=True,
        auditor_AST_unchanged_except_retention_policy_and_empty_eligibility=True,
        corrupt_nonempty_retained_traces_rejected=4,
        full_XML_fixture_validation_complete=False,
        full_neuron_causal_experiment_complete=False, promoted=False)
    (out/'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'bindings'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
