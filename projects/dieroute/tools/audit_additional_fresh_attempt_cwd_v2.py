"""Independently check one fresh attempt's final route and stage receipts."""
import argparse
import contextlib
import csv
import importlib.util
import json
from pathlib import Path
from prepare_additional_fresh_parent import digest
from audit_prospective_final_native_identity import verify_quality
import audit_private_tree_capacity as capacity


def audit(attempt, output):
    attempt, output = attempt.resolve(), output.resolve()
    refs = {}

    def sha(path):
        path = Path(path).resolve()
        refs[str(path)] = digest(path)
        return refs[str(path)]

    def read(path):
        sha(path)
        return json.loads(Path(path).read_text())

    def check_guard(directory):
        protocol = read(directory / 'native_protocol.json')
        terminal = read(directory / 'native_terminal.json')
        assert len(protocol['cases']) == len(terminal['results']) == 1
        case, result = protocol['cases'][0], terminal['results'][0]
        assert case['label'] == result['label']
        assert len(case['commands']) == len(result['steps'])
        for (name, command), step in zip(case['commands'].items(), result['steps']):
            receipt = read(directory / case['label'] / (name + '.terminal.json'))
            launch = read(directory / case['label'] / (name + '.launch.json'))
            assert receipt == step and step['command'] == command
            assert step['returncode'] == 0 and step['memory_guard_stop_reason'] is None
            assert all(receipt[k] == launch[k] for k in launch)
        for name, expected in protocol['source_sha256'].items():
            assert sha(name) == expected, name

    failed = read(attempt / 'initial/execution/initial.terminal.json')
    assert failed['returncode'] == 1 and failed['memory_guard_stop_reason'] is None
    assert not (attempt / 'initial/manifest.json').exists()
    diagnosis = read(attempt / 'initial_entry_failure_diagnosis.json')
    assert diagnosis['initial_algorithm_executed'] is False
    for name, expected in diagnosis['source_sha256'].items():
        assert sha(name) == expected, name
    for directory in [attempt, attempt / 'capacity', attempt / 'capacity_review_guard',
                      attempt / 'initial_v2', attempt / 'initial_v2_review_guard',
                      attempt / 'fixed_followup_v2']:
        check_guard(directory)
    final_manifest = read(attempt / 'fixed_followup_v2/manifest.json')
    final = read(final_manifest['final_report'])
    for name, expected in final['source_sha256'].items():
        assert sha(name) == expected, name
    for command in final_manifest['commands']:
        assert command['returncode'] == 0
    case, = read(attempt / 'initial_v2/protocol.json')['cases']
    if 'current_state' in final:
        tree = Path(final['current_state']['tree'])
        leaf = read(final['current_state']['audit'])
        assert all(leaf['checks'].values())
    elif 'final_tree' in final:
        tree = Path(final['final_tree'])
    else:
        leaf_path = Path(final['selected_native_audit'])
        leaf = read(leaf_path)
        assert all(leaf['checks'].values())
        tree = leaf_path.parent / 'candidate/route.route_trees.csv'
    quality_path = tree.parent / 'native_validation/validation.json'
    quality = verify_quality(quality_path, Path(case['native_case']), sha)
    output.mkdir(exist_ok=False)
    pre = output / 'capacity'
    pre.mkdir()
    (pre / 'protocol.json').write_text(json.dumps({
        'candidate_tree': str(tree), 'baseline_tree': case['native_tree'],
        'connections': case['connections'], 'resources': case['input_prefix'] + '.resources',
        'node_die': case['topology_prefix'] + '.node_die'}, indent=2) + '\n')
    with (output / 'capacity.stdout').open('x') as log, contextlib.redirect_stdout(log):
        capacity.main(pre)
    checked = read(pre / 'independent_preflight.json')
    assert checked['candidate']['overused_resources'] == 0
    assert checked['candidate']['all_sinks_and_nodes_reachable']
    root = Path(__file__).resolve().parents[1]
    exporter = root / 'work/additional_circuit_full_graph_roundtrip_20261020/tools/export_native_vpr_tree.py'
    spec = importlib.util.spec_from_file_location('fresh_final_native_exporter', exporter)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sha(exporter)
    route = Path(quality['command'][quality['command'].index('--route_file') + 1])
    if not route.is_absolute():
        route = quality_path.parent / route
    actual = module.extract(route)
    baseline = module.extract(Path(case['native_case']) / 'circuit.route')
    expected = {}
    with tree.open() as stream:
        for row in csv.DictReader(stream):
            net = int(row['net_id'])
            entry = expected.setdefault(net, {'source': int(row['source']), 'edges': set()})
            assert entry['source'] == int(row['source'])
            entry['edges'].add((int(row['parent']), int(row['child'])))
    assert set(actual) == set(expected) == set(baseline)
    for net, native in actual.items():
        assert native['source'] == expected[net]['source']
        assert {(a, b) for a, b, switch in native['edges']} == expected[net]['edges']
        assert sorted(native['sinks']) == sorted(baseline[net]['sinks'])
    checks = {'native_legal': True, 'capacity': True, 'complete_native_tree_identity': True,
              'wirelength': quality['total_wirelength'] <= case['baseline_wirelength'],
              'CPD': quality['critical_path_delay_ns'] <= case['baseline_cpd_ns'],
              'modeled_transitions': checked['candidate']['layer_transitions'] <=
                                     checked['baseline']['layer_transitions']}
    sha(tree)
    result = {'status': 'one_fresh_attempt_stage_receipts_and_final_native_route_reviewed',
              'label': case['label'], 'checks': checks, 'joint_quality_pass': all(checks.values()),
              'wirelength': quality['total_wirelength'], 'cpd_ns': quality['critical_path_delay_ns'],
              'final_tree_sha256': sha(tree), 'source_sha256': refs,
              'scope': 'One fresh integration attempt only; not five repeats, runtime speedup, '
                       'physical SLL or board proof. Failed attempts must remain in cohort.',
              'research_complete': False}
    (output / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.attempt, args.output)))
