"""Review a repaired fresh parent without inventing an additional sweep."""
import argparse
import json
from pathlib import Path
from prepare_additional_fresh_parent import digest


def audit(attempt, parameter_source, case_source, output):
    attempt, parameter_source, case_source = (
        p.resolve() for p in (attempt, parameter_source, case_source))
    parameters = json.loads(parameter_source.read_text())
    for name, expected in parameters['source_sha256'].items():
        assert digest(name) == expected, name
    label = json.loads((attempt / 'parent_preparation.json').read_text())['label']
    case, = [c for c in json.loads(case_source.read_text())['cases'] if c['label'] == label]
    metrics = json.loads((attempt / 'parent/route.json').read_text())
    assert metrics['iterations'] == parameters['maximum_total_routing_sweeps']
    terminal = json.loads((attempt / 'capacity_audit.terminal.json').read_text())
    assert terminal['returncode'] == 0 and terminal['memory_guard_stop_reason'] is None
    review_path = attempt / 'independent_native_review.json'
    review = json.loads(review_path.read_text())
    for name, expected in review['source_sha256'].items():
        assert digest(name) == expected, name
    row, = review['rows']
    assert row['label'] == label and row['checks']['native_legal']
    assert row['checks']['zero_overuse'] and row['checks']['all_net_exact_candidate_tree_writeback']
    assert row['checks']['all_sink_pin_identity']
    quality_path = attempt / 'capacity/native_validation/validation.json'
    quality = json.loads(quality_path.read_text())
    assert quality['total_wirelength'] == row['wirelength']
    assert quality['critical_path_delay_ns'] == row['cpd_ns']
    assert row['baseline_wirelength'] == case['baseline_wirelength']
    assert row['baseline_cpd_ns'] == case['baseline_cpd_ns']
    result = {
        'status': 'fresh_parent_budget_exhausted_capacity_outcome_reviewed',
        'label': label, 'parent_iterations': metrics['iterations'],
        'maximum_total_routing_sweeps': parameters['maximum_total_routing_sweeps'],
        'additional_initial_sweeps_executed': 0,
        'initial_stage_status': 'skipped_original_sweep_budget_exhausted',
        'joint_quality_pass': row['joint_quality_pass'], 'checks': row['checks'],
        'quality': quality, 'final_tree': str(attempt / 'capacity/repaired.route_trees.csv'),
        'final_native_route': str(attempt / 'capacity/native.route'),
        'crossings': row['modeled_layer_transitions'],
        'source_sha256': {str(p): digest(p) for p in [parameter_source, case_source,
            attempt / 'parent/route.json', attempt / 'capacity_audit.terminal.json',
            review_path, quality_path, Path(__file__).resolve()]},
        'scope': 'Explicit budget-exhausted branch; no sweep/refresh execution asserted. '
                 'Raw parent failure retained. Fixed followup and final attempt review '
                 'remain separate, as do five repetitions and board measurements.',
        'research_complete': False,
    }
    with output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['attempt', 'parameter_source', 'case_source', 'output']:
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.attempt, args.parameter_source, args.case_source, args.output)))
