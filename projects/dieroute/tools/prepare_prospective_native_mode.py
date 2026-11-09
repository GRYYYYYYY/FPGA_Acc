"""Prepare one preregistered native-guided mode without changing its policy."""
from pathlib import Path
from decimal import Decimal
import argparse
import csv
import hashlib
import json
import subprocess
import sys
import audit_private_tree_capacity as capacity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['baselines', 'roundtrip', 'costs', 'case_protocol', 'initial_audit']:
        parser.add_argument(name, type=Path)
    parser.add_argument('mode', choices=['wirelength', 'delay'])
    parser.add_argument('output', type=Path)
    parser.add_argument('--prior-mode', type=Path)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    policy_path = args.baselines.resolve() / 'candidate_policy.json'
    policy = json.loads(policy_path.read_text())
    sources = {}

    def sha(path):
        path = Path(path).resolve()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        sources[str(path)] = digest
        return digest

    def bind(paths):
        return {str(Path(p).resolve()): sha(p) for p in paths}

    def write(path, value):
        with Path(path).open('x') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')

    def run(command, name):
        with (output / (name + '.log')).open('x') as stream:
            subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT, check=True)

    for name, expected in policy['source_sha256'].items():
        assert sha(name) == expected, name
    case_protocol = json.loads(args.case_protocol.read_text())
    case, = case_protocol['cases']
    initial = json.loads(args.initial_audit.read_text())
    label = case['label']
    assert initial['label'] == label and initial['status'] == 'prospective_initial_case_decisions_and_native_provenance_reviewed'
    assert label in ['apex2_seed' + str(seed) for seed in policy['cohort']['seeds']]
    for name, expected in initial['source_sha256'].items():
        assert sha(name) == expected, name
    assert Path(case['native_case']).resolve() == (args.baselines / label).resolve()
    assert Path(case['connections']).resolve() == (args.roundtrip / label / 'connections.csv').resolve()
    assert Path(case['input_prefix'] + '.nodes').resolve() == (args.costs / label / 'input.nodes').resolve()
    config = policy['candidate_policy']
    if args.mode == 'wirelength':
        assert args.prior_mode is None and not initial['joint_quality_pass']
        current = {'tree': initial['final_tree'], 'route': initial['final_native_route']}
    else:
        assert args.prior_mode is not None
        prior_protocol = json.loads((args.prior_mode / 'protocol.json').read_text())
        assert prior_protocol['prospective_label'] == label and prior_protocol['prospective_mode'] == 'wirelength'
        prior = json.loads((args.prior_mode / 'manifest.json').read_text())
        assert prior['status'].startswith('experiment_terminal_')
        current = dict(prior['current_state'])
    tree = Path(current['tree'])
    quality_file = tree.parent / 'native_validation/validation.json'
    quality = json.loads(quality_file.read_text())
    assert quality['legal'] and sha(current['route']) == quality['inputs']['route_sha256']
    if args.prior_mode is None:
        assert quality == initial['quality']
    else:
        assert (quality['critical_path_delay_ns'], quality['total_wirelength']) == (current['cpd_ns'], current['wirelength'])
    assert quality['baseline_wirelength'] == case['baseline_wirelength'] and quality['baseline_cpd_ns'] == case['baseline_cpd_ns']
    native = Path(case['native_case'])
    for key, name in [('arch', 'architecture.xml'), ('circuit', 'circuit.blif'), ('net', 'circuit.net'),
                      ('place', 'circuit.place'), ('rr_graph', 'rr_graph.xml')]:
        assert sha(native / name) == quality['inputs'][key + '_sha256']
    native_baseline = json.loads((native / 'run.json').read_text())
    assert Path(case_protocol['vpr']).resolve() == Path(native_baseline['sources']['vpr']['path']).resolve()
    output.mkdir()
    evidence = output / 'initial_evidence'
    evidence.mkdir()
    pre = {'candidate_tree': str(tree), 'baseline_tree': case['native_tree'],
           'connections': case['connections'], 'resources': case['input_prefix'] + '.resources',
           'node_die': case['topology_prefix'] + '.node_die'}
    write(evidence / 'protocol.json', pre)
    capacity.main(evidence)
    allocations = json.loads((evidence / 'independent_preflight.json').read_text())
    checks = {'native_legal': quality['legal'], 'capacity': allocations['candidate']['overused_resources'] == 0,
              'wirelength': quality['total_wirelength'] <= case['baseline_wirelength'],
              'CPD': quality['critical_path_delay_ns'] <= case['baseline_cpd_ns'],
              'modeled_transitions': allocations['candidate']['layer_transitions'] <= allocations['baseline']['layer_transitions']}
    assert checks['capacity'] and checks['wirelength'] and checks['modeled_transitions'] and not all(checks.values())
    current.update(cpd_ns=quality['critical_path_delay_ns'], wirelength=quality['total_wirelength'],
                   model_crossings=allocations['candidate']['layer_transitions'], audit=str(evidence / 'native_audit.json'))
    write(evidence / 'native_audit.json', {'status': 'prospective_mode_initial_native_authority_verified',
          'checks': checks, 'quality': quality, 'source_sha256': bind([quality_file, tree, current['route'],
          args.initial_audit, evidence / 'independent_preflight.json']), 'research_complete': False})
    native = Path(case['native_case'])
    device = policy['cohort']['device']
    width = policy['cohort']['channel_width']
    vpr = case_protocol['vpr']

    def native_command(route, work):
        cmd = ['python3', case_protocol['validator'], '--vpr', vpr, '--device', device]
        for flag, name in [('arch', 'architecture.xml'), ('circuit', 'circuit.blif'), ('net', 'circuit.net'),
                           ('place', 'circuit.place'), ('rr-graph', 'rr_graph.xml')]:
            cmd += ['--' + flag, str(native / name)]
        return cmd + ['--route', str(route), '--channel-width', str(width), '--work-dir', str(work),
                      '--baseline-wirelength', str(case['baseline_wirelength']), '--baseline-cpd-ns', str(case['baseline_cpd_ns'])]

    if args.mode == 'wirelength':
        observation = output / 'baseline_observation'
        observation.mkdir()
        (observation / 'baseline').mkdir()
        query = observation / 'native_probe.input.csv'
        with query.open('x') as stream:
            writer = csv.DictWriter(stream, fieldnames=['iteration', 'task_id', 'net_id', 'source', 'sink', 'routed', 'delay_ps', 'criticality_q'])
            writer.writeheader()
            for row in csv.DictReader(Path(case['connections']).open()):
                writer.writerow(dict(iteration=0, task_id=row['id'], net_id=row['net_id'], source=row['source'], sink=row['sink'], routed=0, delay_ps=0, criticality_q=0))
        cmd = native_command(native / 'circuit.route', observation / 'baseline/native_validation')
        obs = {'cases': [{'name': 'baseline', 'command': cmd, 'environment': {
               'PERSISTROUTE_VPR_TIMING_INPUT': str(query), 'PERSISTROUTE_VPR_TIMING_OUTPUT': str(observation / 'baseline/native_observations.csv')}}],
               'connections': case['connections'], 'source_sha256': bind([Path(v) for v in cmd if Path(v).is_file()] + [query, Path(case['connections'])]),
               'scope': 'Read-only baseline routed0 observations for one frozen prospective case.'}
        write(observation / 'protocol.json', obs)
        for tool in ['run_native_RC_observations.py', 'audit_native_RC_observations.py']:
            run(['python3', str(root / 'tools' / tool), str(observation)], tool)
        observed_quality = json.loads((observation / 'baseline/native_validation/validation.json').read_text())
        assert observed_quality['total_wirelength'] == case['baseline_wirelength'] and observed_quality['critical_path_delay_ns'] == case['baseline_cpd_ns']
        baseline_observations = observation / 'baseline/native_observations.csv'
        weights = output / 'wirelength_weights'
        run(['python3', str(root / 'tools/export_vpr_wirelength_weights.py'), str(native / 'rr_graph.xml'), case['input_prefix'] + '.nodes', str(weights),
             '--case', case['native_tree'], str(args.roundtrip / label / 'native_validation/validation.json'),
             '--case', str(tree), str(quality_file)], 'wirelength_weights')
        weight_file = weights / 'node_wirelength.u16'
    else:
        baseline_observations = Path(prior_protocol['baseline_observations'])
        old_obs = json.loads(Path(prior_protocol['observation_template']).read_text())
        query = Path(old_obs['cases'][0]['environment']['PERSISTROUTE_VPR_TIMING_INPUT'])
        weight_file = Path(json.loads(Path(prior_protocol['exchange_template']).read_text())['wirelength_weights'])
    parent_case = {'name': 'parent', 'command': native_command(current['route'], output / 'unused_parent_validation'),
                   'environment': {'PERSISTROUTE_VPR_TIMING_INPUT': str(query), 'PERSISTROUTE_VPR_TIMING_OUTPUT': str(output / 'unused_parent_observations.csv')}}
    write(output / 'observation_template.json', {'cases': [parent_case], 'connections': case['connections'],
          'parent_tree': str(tree), 'source_sha256': bind([query, Path(case['connections']), baseline_observations]),
          'scope': 'Per-stage runner replaces parent route/output paths before execution.'})
    exchange = dict(candidate_tree=str(tree), baseline_tree=case['native_tree'], connections=case['connections'],
                    nodes=case['input_prefix'] + '.nodes', edges=case['input_prefix'] + '.edges', resources=case['input_prefix'] + '.resources',
                    boxes=case['topology_prefix'] + '.node_box', node_die=case['topology_prefix'] + '.node_die',
                    box_margin=config['diagnosis_box_margin'], maximum_expanded_per_sink=config['maximum_labels_per_sink'],
                    maximum_net_order_attempts=config['maximum_net_order_attempts'], unboxed_search=config['unboxed_exchange_search'],
                    search_objective=args.mode, baseline_cpd_ps=int(Decimal(str(case['baseline_cpd_ns'])) * 1000),
                    global_crossing_cap=allocations['baseline']['layer_transitions'],
                    connection_ceiling_cpd_ps=int(Decimal(str(quality['critical_path_delay_ns'])) * 1000),
                    blockers_first=True, reverse_target_remaining_sinks=True, wirelength_weights=str(weight_file),
                    critical_tasks=[], arms=[], blocked_paths=str(output / 'unused_blocked_paths.json'),
                    native_parent_observations=str(output / 'unused_parent_observations.csv'))
    inputs = [Path(exchange[k]) for k in ['candidate_tree', 'baseline_tree', 'connections', 'nodes', 'edges', 'resources', 'boxes', 'node_die', 'wirelength_weights']]
    exchange['source_sha256'] = bind(inputs)
    write(output / 'exchange_template.json', exchange)
    diagnosis = {k: exchange[k] for k in ['candidate_tree', 'baseline_tree', 'connections', 'nodes', 'edges', 'resources', 'boxes', 'box_margin', 'maximum_expanded_per_sink', 'critical_tasks']}
    diagnosis['source_sha256'] = bind(inputs)
    write(output / 'diagnosis_template.json', diagnosis)
    commands = {'writer': ['python3', case_protocol['writer'], str(native / 'circuit.route'), str(native / 'rr_graph.xml'), case['connections'], 'ARM_TREE', 'ARM_DIRECTORY/native.route'],
                'native': native_command('ARM_DIRECTORY/native.route', 'ARM_DIRECTORY/native_validation')}
    native_template = {k: exchange[k] for k in ['candidate_tree', 'baseline_tree', 'connections', 'resources', 'node_die']}
    native_template.update(arms=[{'name': 'candidate', 'nets': []}], commands=commands,
                           source_sha256=bind(inputs), scope='Native writer/validator with original frozen case budgets.')
    write(output / 'native_template.json', native_template)
    actor = root / 'tools/run_ranked_objective_native_refinement.py'
    protocol = {'status': 'frozen_before_launch', 'maximum_stages': config['maximum_stages_each_mode'], 'initial_state': current,
                'observation_template': str(output / 'observation_template.json'), 'diagnosis_template': str(output / 'diagnosis_template.json'),
                'exchange_template': str(output / 'exchange_template.json'), 'native_template': str(output / 'native_template.json'),
                'baseline_observations': str(baseline_observations), 'initial_exhausted_tasks': [],
                'acceptance_objective': ['native_CPD_ns', 'native_wirelength', 'modeled_crossings'],
                'prospective_label': label, 'prospective_mode': args.mode,
                'scope': 'Preregistered ranked/lexicographic mode, unchanged algorithms and original baseline gates. Paths/data only; no tuning, resampling or board claim.',
                'source_sha256': bind([actor, policy_path, args.case_protocol, args.initial_audit, baseline_observations,
                                      output / 'observation_template.json', output / 'diagnosis_template.json', output / 'exchange_template.json',
                                      output / 'native_template.json', evidence / 'native_audit.json', Path(__file__).resolve()] + inputs)}
    write(output / 'protocol.json', protocol)
    print(json.dumps({'prepared_mode': args.mode, 'label': label, 'maximum_stages': protocol['maximum_stages']}), flush=True)
    if args.run:
        subprocess.run(['python3', str(actor), str(output)], cwd=root, check=True)


if __name__ == '__main__':
    main()
