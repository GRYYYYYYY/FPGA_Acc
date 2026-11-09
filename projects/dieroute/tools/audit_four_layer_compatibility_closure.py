"""Join source, build dependency and observed route compatibility evidence."""
from pathlib import Path
import argparse
import hashlib
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('compatibility', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build = args.build.resolve()
    compatibility = args.compatibility.resolve()
    refs = {}

    def sha(path):
        path = Path(path)
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                digest.update(block)
        refs[str(path)] = digest.hexdigest()
        return refs[str(path)]

    def read(path, verify_sources=False):
        path = Path(path)
        value = json.loads(path.read_text())
        sha(path)
        if verify_sources:
            for name, expected in value['source_sha256'].items():
                assert sha(name) == expected, name
        return value

    delta = read(build / 'independent_layer_delta_audit.json', True)
    assert delta['status'] == 'verified_exact_single_header_layer_bound_extension'
    dependency = read(build / 'build_dependency_audit.json', True)
    assert dependency['status'] == 'new_frozen_vpr_sources_compiler_dependencies_and_link_inputs_audited'
    state = read(build / 'manifest.json')
    assert state['status'] == 'new_source_bound_build_completed_dependency_and_native_compatibility_audits_required'
    assert sha(state['binary']) == state['binary_sha256'] == dependency['binary_sha256']
    assert Path(dependency['binary']).resolve() == Path(state['binary']).resolve()
    protocol = read(compatibility / 'protocol.json', True)
    assert Path(protocol['source_bound_build_audit']).resolve() == build / 'build_dependency_audit.json'
    terminal = read(compatibility / 'manifest.json')
    assert terminal['status'] == 'source_bound_compatibility_terminal_requires_interpretation'
    assert [g['label'] for g in protocol['groups']] == ['elliptic', 'apex2']
    observed = []
    for group in protocol['groups']:
        directory = Path(group['directory'])
        audit = read(directory / 'compatibility_audit.json', True)
        native = read(directory / 'independent_audit.json', True)
        case_protocol = read(directory / 'protocol.json', True)
        assert native['status'] == 'native_routed0_observations_provenance_and_quality_reviewed'
        assert audit['status'] == 'all_observed_routes_source_bound_native_and_timing_compatible'
        assert [v['name'] for v in audit['routes']] == ['baseline', 'candidate']
        for case in case_protocol['cases']:
            if case['name'].endswith('_source_bound'):
                command = case['command']
                assert Path(command[command.index('--vpr') + 1]).resolve() == Path(state['binary']).resolve()
        for route in audit['routes']:
            assert route['legacy_native_legal'] and route['source_bound_native_legal']
            assert route['metrics_identical'] and route['timing_CSV_bytes_identical']
            assert all(v == 0 for v in route['maximum_absolute_field_differences'].values())
        observed.append({'group': group['label'], 'routes': audit['routes']})
    sha(Path(__file__).resolve())
    result = {
        'status': 'source_delta_and_observed_four_route_compatibility_verified',
        'binary_sha256': state['binary_sha256'],
        'observations': observed,
        'source_sha256': refs,
        'scope': 'Two circuits, baseline and candidate each. Exact printed native metrics and rounded timing CSV compatibility. Dependency audit retained separately; no historical binary source identity, universal equivalence, algorithm generalization or board performance claim.',
        'research_complete': False,
    }
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'circuits': len(observed), 'routes': 4}))


if __name__ == '__main__':
    main()
