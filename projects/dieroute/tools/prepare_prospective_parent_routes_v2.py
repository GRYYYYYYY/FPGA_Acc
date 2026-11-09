"""Adapt transitively frozen parent recipes to prospective data paths only."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baselines', type=Path)
    parser.add_argument('roundtrip', type=Path)
    parser.add_argument('costs', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    baselines, roundtrip, costs, output = [p.resolve() for p in [args.baselines, args.roundtrip, args.costs, args.output]]
    refs = {}

    def sha(path):
        path = Path(path).resolve()
        key = str(path)
        if key not in refs:
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1048576), b''):
                    digest.update(block)
            refs[key] = digest.hexdigest()
        return refs[key]

    def load(path):
        sha(path)
        return json.loads(Path(path).read_text())

    policy = load(baselines / 'candidate_policy.json')
    for path, expected in policy['source_sha256'].items():
        assert sha(path) == expected, path
    old_parameters = Path(policy['candidate_policy']['parameter_source'])
    parameters = load(old_parameters)
    for path, expected in parameters['source_sha256'].items():
        assert sha(path) == expected, path
    old = root / 'work/reserved_apex2_parent_20261017'
    old_manifest = old / 'parents/apex2_seed5/manifest.json'
    assert sha(old_manifest) == parameters['source_sha256'][str(old_manifest)]
    parent = load(old_manifest)
    template = old / 'recipes/apex2_seed5/pair.json'
    assert sha(template) == parent['source_sha256'][str(template)]
    for path, expected in parent['source_sha256'].items():
        assert sha(path) == expected, path
    original = load(template)
    cost_audit = load(costs / 'independent_audit.json')
    assert cost_audit['status'] == 'five_prospective_apex2_native_indexed_cost_maps_and_all_edge_rebases_independently_verified'
    labels = [row['label'] for row in cost_audit['cases']]
    assert labels == ['apex2_seed' + str(seed) for seed in policy['cohort']['seeds']]
    committed_vpr = [Path(name) for name in parent['source_sha256'] if Path(name).name == 'vpr' and Path(name).parent.name == 'vpr']
    assert len(committed_vpr) == 1
    build = committed_vpr[0].parents[2]
    binary_audit = load(build / 'build_dependency_audit.json')
    assert sha(binary_audit['binary']) == binary_audit['binary_sha256']
    assert sha(binary_audit['binary']) == parent['source_sha256'][binary_audit['binary']]
    assert b'PERSISTROUTE_VPR_TIMING_REQUEST_FIFO' in Path(binary_audit['binary']).read_bytes(), 'Frozen parent timing engine must support FIFO sessions'
    runner = root / 'work/sb3_fixed_feedback_pair_20261015/native_tools/run_persistent_timing_online.py'
    output.mkdir()
    (output / 'recipes').mkdir()
    (output / 'parents').mkdir()
    commands, adaptations = [], []
    for label in labels:
        case = baselines / label
        folder = output / 'recipes' / label
        folder.mkdir()
        shutil.copytree(template.parent / 'source', folder / 'source', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copyfile(costs / label / 'input.tasks', folder / 'input.tasks')
        pair = json.loads(json.dumps(original))
        step = pair['steps'][0]
        command = step['command']
        command[1] = str(costs / label / 'input')
        command[2] = str(roundtrip / label / 'topology')
        command[3] = str(output / 'unused_output')
        step['cwd'] = str(output)
        environment = step['routing_environment']
        frozen_dieroute = {k: v for k, v in environment.items() if k.startswith('DIEROUTE_')}
        for key, name in [('ARCH', 'architecture.xml'), ('CIRCUIT', 'circuit.blif'), ('NET', 'circuit.net'),
                          ('PLACE', 'circuit.place'), ('ROUTE', 'circuit.route'), ('RR_GRAPH', 'rr_graph.xml')]:
            environment['PERSISTROUTE_VPR_' + key] = str(case / name)
        environment['PERSISTROUTE_VPR_BIN'] = binary_audit['binary']
        assert frozen_dieroute == {k: v for k, v in environment.items() if k.startswith('DIEROUTE_')}
        recipe = folder / 'pair.json'
        recipe.write_text(json.dumps(pair, indent=2) + '\n')
        commands.append({'label': label, 'command': [sys.executable, str(runner), str(recipe), str(build), str(output / 'parents' / label)]})
        adaptations.append({'label': label, 'all_DIEROUTE_parameters_unchanged': True,
                            'parent_binary_sha256': sha(command[0]), 'recipe_sha256': sha(recipe)})
        for path in list(folder.rglob('*')) + [Path(command[0]), costs / label / 'input.nodes', costs / label / 'input.edges', costs / label / 'input.resources', roundtrip / label / 'topology.node_die']:
            if path.is_file():
                sha(path)
    for name in ['run_persistent_timing_online.py', 'persistent_vpr_timing.py', 'persistent_timing_client.py']:
        sha(runner.with_name(name))
    sha(costs / 'protocol.json')
    sha(Path(__file__).resolve())
    protocol = {'status': 'frozen_before_launch', 'commands': commands, 'inputs': refs,
                'scope': 'All five prospective parents; old seed5 parameter protocol commits old parent manifest, which commits recipe/binary. All bound files verified; data paths adapted; original transitively committed FIFO timing-engine binary restored, DIEROUTE parameters unchanged. Initial parent routing only, no candidate quality or acceleration claim.', 'research_complete': False}
    (output / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    script = (old / 'supervise.py').read_text().replace('five_reserved_apex2_parent_attempts_terminal', 'five_prospective_apex2_parent_attempts_terminal')
    script = script.replace("p=Path(__file__).resolve().parent;x=", "p=Path(__file__).resolve().parent;assert not (p/'manifest.json').exists();x=")
    (output / 'supervise.py').write_text(script)
    (output / 'launch_protocol.json').write_text(json.dumps({'inputs': {str(path): sha(path) for path in [output / 'protocol.json', output / 'supervise.py']}}, indent=2) + '\n')
    (output / 'adaptation_review.json').write_text(json.dumps({'status': 'transitive_policy_binding_and_unchanged_parent_parameters_verified', 'cases': adaptations, 'source_sha256': refs, 'research_complete': False}, indent=2) + '\n')
    print(json.dumps({'prepared_parents': len(commands), 'directory': str(output)}), flush=True)
    if args.run:
        subprocess.run([sys.executable, str(output / 'supervise.py')], cwd=root, check=True)


if __name__ == '__main__':
    main()
