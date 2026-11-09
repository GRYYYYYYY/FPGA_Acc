"""Close the exposed-XTEA warm update experiment without mixing cost scopes."""
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure


def main():
    bindings = closure([Path(__file__)])

    def admit(directory, flag=None):
        path = R / 'experiments' / directory / 'verification.json'
        value = json.loads(path.read_text())
        if flag:
            assert value[flag]
        for name, digest in value['bindings'].items():
            assert sha(name) == digest, name
            assert name not in bindings or bindings[name] == digest
            bindings[name] = digest
        bindings[str(path)] = sha(path)
        return value

    pair = admit('xtea_warm_update_pair_v1_2026-10-13', 'both_complete_models_and_all_audits_pass')
    warm = admit('xtea_swap_warm_seed_v1_2026-10-13', 'old_unaffected_records_exactly_preserved')
    seeds = admit('xtea_warm_native_seed_preparation_v1_2026-10-13', 'complete_required_connection_partition_and_subset_capacity_pass')
    native = admit('xtea_warm_native_comparison_v1_2026-10-13', 'all_three_native_physical_and_canonical_pass')
    quality = admit('xtea_warm_update_hotspots_v1_2026-10-13', 'same_graph_endpoints_and_frozen_native_labels_pass')
    assert quality['metric_vectors_independently_recomputed'] == 12
    assert pair['initial_and_floors_byte_equal_shared_warm_seed']
    native_rows = {r['arm']: r for r in native['rows']}
    seed_rows = {r['arm']: r for r in seeds['rows']}
    model_rows = {r['arm']: r for r in pair['results']}
    rows = {}
    cold = native_rows['cold']
    for arm in ['all', 'local']:
        model, seed, routed = model_rows[arm], seed_rows[arm], native_rows[arm]
        assert routed['exit_status'] == 0 and routed['canonical']['semantic_consistency_gate_pass']
        assert seed['selected_connections'] + seed['pending_connections'] == 2450
        components = {
            'warm_seed_preparation_including_its_checks': warm['whole_preparation_seconds'],
            'model_including_setup_and_output': model['total_paid_resident_seconds'],
            'native_seed_selection_and_serialization': seed['selection_serialization_seconds'],
            'native_process': routed['native_process_seconds'],
        }
        rows[arm] = dict(
            primary_search_calls=sum(r['primary_search_calls'] for r in model['rounds']),
            sketch_overflow=model['rounds'][-1]['overflow'],
            prediction_metrics=quality['metrics']['warm_' + arm + '_sketch'],
            native={k: routed[k] for k in ['wirelength', 'diagnostic_cpd_ns', 'iterations', 'native_process_seconds']},
            component_seconds=components,
            component_sum_seconds=sum(components.values()),
            component_sum_over_cold_native=sum(components.values()) / cold['native_process_seconds'],
            native_wirelength_change_from_cold=routed['wirelength'] - cold['wirelength'],
        )
    all_row, local_row = rows['all'], rows['local']
    result = dict(
        bindings=bindings,
        all_bound_sources_inputs_outputs_unchanged=True,
        rows=rows,
        cold_native={k: cold[k] for k in ['wirelength', 'diagnostic_cpd_ns', 'iterations', 'native_process_seconds']},
        local_over_all_model_seconds=model_rows['local']['total_paid_resident_seconds'] / model_rows['all']['total_paid_resident_seconds'],
        local_over_all_search_calls=local_row['primary_search_calls'] / all_row['primary_search_calls'],
        local_minus_all_sketch_overflow=local_row['sketch_overflow'] - all_row['sketch_overflow'],
        promote_as_end_to_end_acceleration=False,
        conclusions=[
            'Local scheduling reduces this single-run model cost, but concrete resource prediction is worse than allNET scheduling; spatial top20 precision improves while rank/MAE worsen.',
            'Both seed arms produce fully legal native routes with slightly less wirelength and equal printed diagnostic CPD versus cold; neither establishes total time gain.',
            'This is one real placement swap on an exposed development design, with a fixed pre-move timing snapshot; no placement acceptance policy or unseen-family result is established.',
        ],
        cost_scope={
            'component_sum_is_fresh_continuous_workflow_timer': False,
            'single_run_shared_host_measurements': True,
            'separate_unincluded_costs': [
                'Original packing/placement/RR capture and conversion',
                'Construction of previous sketch and native timing snapshot',
                'Move generation, endpoint extraction and metadata remapping',
                'External model physical/event audits and native canonical audits',
                'Driver gaps and costs outside individually recorded components',
            ],
            'diagnostic_cpd_only': 'Experimental asynchronous architecture timing is not fully characterized.',
        },
        next_experiment='Freeze a prospective fixed-placement-shell SKETCH on/off candidate cohort and decision rule before new native outcomes. Include baseline retention, identical native acceptance gates and complete cost scopes.',
    )
    assert all(sha(p) == h for p, h in bindings.items())
    out = R / 'experiments/xtea_warm_update_hotspots_v1_2026-10-13/research_decision_v1.json'
    with out.open('x') as f:
        f.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['bindings', 'rows']}, indent=2))


if __name__ == '__main__':
    main()
