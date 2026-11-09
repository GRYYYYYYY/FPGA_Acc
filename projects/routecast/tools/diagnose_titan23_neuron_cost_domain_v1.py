"""Reproduce the current u64 admission failure using an observed Titan arc cost."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace

R = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(R / 'tools'), str(R / 'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from structural_objective_search_v1 import Search


def main():
    p = R / 'experiments/titan23_neuron_graph_recovery_v1_2026-10-13/lattice_readiness.json'
    v = json.loads(p.read_text())
    assert v['original_XML_all_node_and_edge_identities_and_electrical_values_pass']
    assert all(sha(path) == h for path, h in v['bindings'].items())
    largest = v['maximum_arc_word']
    assert largest >= 2**64 and largest < 2**120
    fields = dict(node_ids=(0, 1), row_offsets=(0, 1, 1), dest_ranks=(1,), edge_ids=(0,), switch_ids=(0,), costs=(1,), capacities=(1, 1))
    rc = SimpleNamespace(increments=(largest,), initial=lambda node: 0)
    binary = R / 'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so'
    try:
        search = Search(fields, rc, binary, (0, 0))
    except ValueError as exc:
        error = str(exc)
        assert error == 'invalid integer costs'
    else:
        search.close()
        raise AssertionError('Expected rejection of the actual >u64 observed cost')
    bindings = {**v['bindings'], str(p): sha(p), **closure([Path(__file__)]), str(binary): sha(binary)}
    cpp = R / 'tools/soft_demand_cpp/tree_workspace_radix_v3.cpp'
    bindings[str(cpp)] = sha(cpp)
    result = dict(
        bindings=bindings,
        original_graph_nodes=v['nodes'], original_graph_edges=v['edges'], exact_scale=v['exact_scale'],
        observed_maximum_arc_integer=largest, observed_maximum_arc_bits=largest.bit_length(),
        current_increment_bits=64, current_raw_distance_bits=64,
        one_ns_budget_integer=v['exact_scale'] // 10**9,
        one_ns_budget_bits=(v['exact_scale'] // 10**9).bit_length(),
        simple_path_upper_bound_bits=v['raw_simple_path_upper_bound'].bit_length(),
        current_structural_search_rejected_observed_scalar=True, rejection=error,
        full_Titan_model_launched=False, original_graph_quantized_or_modified=False,
        next_requirement='Isolated exact wider increment/raw-distance ABI and native-base payload admission; retain node/edge identities, objective, tie order, budgets and frozen policy. Prove legacy full-state parity plus >u64 adversarial paths before full Titan execution.',
        scope='The complete original graph audit observed this arc cost. A two-node admission fixture carrying that exact scalar reproduces the existing constructor guard before any native backend is launched. This proves the frozen current model cannot accept the graph as encoded, not an algorithmic routability failure. Native initialized base-cost and full model remain untested.',
    )
    assert all(sha(path) == h for path, h in bindings.items())
    out = p.parent / 'cost_domain_rejection_v1.json'
    with out.open('x') as f:
        f.write(json.dumps(result, indent=2) + '\n')
    print('TITAN DOMAIN REJECTION REPRODUCED', largest.bit_length(), 'arc bits;', result['one_ns_budget_bits'], 'one-ns budget bits;', result['simple_path_upper_bound_bits'], 'path bound bits', flush=True)


if __name__ == '__main__':
    main()
