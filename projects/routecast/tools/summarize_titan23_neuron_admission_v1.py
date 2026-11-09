"""Close the pre-route physical admission and preserve the real cost-width rejection."""
import json
from pathlib import Path
import sys

R = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(R / 'tools'), str(R / 'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure


def main():
    graph_dir = R / 'experiments/titan23_neuron_graph_recovery_v1_2026-10-13'
    demand_dir = R / 'experiments/titan23_neuron_native_demand_v1_2026-10-13'
    inputs = [
        (R / 'experiments/titan23_neuron_transfer_freeze_v1_2026-10-13/verification.json', 'archive_members_and_local_inputs_byte_identical'),
        (graph_dir / 'neuron/verification.json', 'original_XML_pin_membership_and_full_rooted_tile_footprints_pass'),
        (graph_dir / 'lattice_readiness.json', 'original_XML_all_node_and_edge_identities_and_electrical_values_pass'),
        (graph_dir / 'cost_domain_rejection_v1.json', 'current_structural_search_rejected_observed_scalar'),
        (demand_dir / 'demand/verification.json', 'exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass'),
        (demand_dir / 'pin_manifest/verification.json', 'logical_pin_key_to_native_index_and_XML_physical_identity_pass'),
        (R / 'experiments/rooted_endpoint_geometry_contract_v1_2026-10-13/verification.json', 'all_pass'),
        (R / 'experiments/rooted_endpoint_geometry_contract_v1_2026-10-13/xtea_verification.json', 'original_XML_pin_membership_and_full_rooted_tile_footprints_pass'),
    ]
    bindings = closure([Path(__file__)])
    values = []
    for path, flag in inputs:
        value = json.loads(path.read_text())
        assert value[flag]
        for name, digest in value['bindings'].items():
            assert name not in bindings or bindings[name] == digest
            bindings[name] = digest
        bindings[str(path)] = sha(path)
        values.append(value)
    assert all(sha(p) == h for p, h in bindings.items())
    endpoint, lattice, domain, demand, pins = values[1:6]
    assert endpoint['connections'] == demand['all_queries'] == 89252
    assert pins['connections'] == demand['physical_queries'] == 77106
    assert demand['ignored_queries'] == 12146
    assert endpoint['pin_occurrences_outside_root_point_bbox'] == {'DSP': 7830}
    assert lattice['maximum_arc_word'] == domain['observed_maximum_arc_integer']
    result = dict(
        bindings=bindings, complete_original_mapped_input_physical_and_native_pin_admission_pass=True,
        original_queries=89252, actual_nonignored_routing_queries=77106, actual_native_ignored_queries=12146,
        included_nets=pins['nets'], nodes=lattice['nodes'], edges=lattice['edges'],
        multi_height_DSP_pin_occurrences_proved=7830,
        current_frozen_model_accepted=False, rejection='Exact original RC encoding needs65-bit increments and67-bit one-ns budgets; current input/raw-path ABI is64bit.',
        exact_scale=lattice['exact_scale'], maximum_arc_integer=domain['observed_maximum_arc_integer'],
        original_graph_or_numerical_policy_modified=False, routed_QoR_labels_generated=False,
        native_initialized_criticality_and_base_capture='Separate metadata-only job; pending at this pre-route admission boundary.',
        strict_unseen_family_certified=False,
        preserved_failures=[
            'First driver: pack/place native exit0, generated-file binding AssertionError before RR export. Intermediate expected digests were not persisted; exact differing digest remains unresolved. New post-place snapshot authenticated and natively reloaded in isolated recovery.',
            'Legacy endpoint audit: assumes block root lies in each endpoint bbox. Preserved failure; new audit requires every bbox cell to belong to the same original-grid rooted tile and additionally checks physical pin membership. Actual7830DSP cases, priorXTEA and two-valid/five-rejected geometry fixtures pass.',
        ],
        next_required_work='Exact wider cost/raw-distance/base/price representation with old-case semantic parity and >u64 tests; authenticate native initialized costs and criticalities; then full frozen-policy transfer, independent audits and native QoR. No truncation or policy retuning is justified by this admission failure.',
        scope='Titan23/neuron original mapped netlist and SDC, default StratixIV architecture; full pre-route physical/identity and exact-width evidence only. No original-HDL equivalence, completed unseen-family validation, full prediction, final routing, end-to-end benefit or hardware claim.',
    )
    out = R / 'experiments/titan23_neuron_admission_v1_2026-10-13'
    out.mkdir()
    (out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print('TITAN PRE-ROUTE ADMISSION PASS; FROZEN MODEL COST DOMAIN REJECTED', pins['connections'], 'connections', flush=True)


if __name__ == '__main__':
    main()
