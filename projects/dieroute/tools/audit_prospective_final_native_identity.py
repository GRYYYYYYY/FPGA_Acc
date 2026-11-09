"""Join each reported joint pass to its exact frozen native baseline inputs."""
import hashlib
import json
from pathlib import Path
import sys


def verify_quality(quality_path, native_case, sha):
    quality_path = Path(quality_path)
    sha(quality_path)
    quality = json.loads(quality_path.read_text())
    assert quality['legal'] is True and quality['vpr_exit_status'] == 0
    for key, name in [('arch', 'architecture.xml'), ('circuit', 'circuit.blif'),
                      ('net', 'circuit.net'), ('place', 'circuit.place'), ('rr_graph', 'rr_graph.xml')]:
        assert sha(Path(native_case) / name) == quality['inputs'][key + '_sha256'], key
    command = quality['command']
    assert sha(command[0]) == quality['inputs']['vpr_sha256']
    route = Path(command[command.index('--route_file') + 1])
    if not route.is_absolute():
        route = quality_path.parent / route
    assert sha(route) == quality['inputs']['route_sha256']
    for key, name in [('stdout', 'vpr_analysis.stdout'), ('stderr', 'vpr_analysis.stderr')]:
        assert sha(quality_path.parent / name) == quality[key + '_sha256']
    return quality


def main():
    summary_path, baselines, output = (Path(v).resolve() for v in sys.argv[1:])
    refs = {}

    def sha(path):
        path = Path(path).resolve()
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                h.update(block)
        refs[str(path)] = h.hexdigest()
        return refs[str(path)]

    def read(path):
        sha(path)
        return json.loads(Path(path).read_text())

    summary = read(summary_path)
    assert summary['status'] == 'five_prospective_terminal_reports_aggregated_with_hash_verification'
    assert [v['label'] for v in summary['rows']] == ['apex2_seed' + str(i) for i in range(6, 11)]
    outcomes = []
    for row in summary['rows']:
        if not row['joint_quality_pass']:
            outcomes.append({'label': row['label'], 'status': 'no_joint_pass_claim', 'classification': row['classification']})
            continue
        report = read(row['final_report'])
        status = report['status']
        if status == 'prospective_initial_case_decisions_and_native_provenance_reviewed':
            quality_path = Path(report['final_tree']).parent / 'native_validation/validation.json'
        else:
            if status == 'prospective_native_mode_acceptance_orders_and_native_wirelength_reviewed':
                leaf_path = Path(report['current_state']['audit'])
            else:
                assert status == 'prospective_capacity_fallback_mixture_capacity_and_native_selection_reviewed'
                leaf_path = Path(report['selected_native_audit'])
            leaf = read(leaf_path)
            assert all(leaf['checks'].values())
            quality_path = leaf_path.parent / 'candidate/native_validation/validation.json'
        quality = verify_quality(quality_path, baselines / row['label'], sha)
        metrics = row['final_metrics']
        assert quality['total_wirelength'] == metrics['wirelength'] <= row['baseline']['wirelength']
        assert quality['critical_path_delay_ns'] == metrics['cpd_ns'] <= row['baseline']['cpd_ns']
        outcomes.append({'label': row['label'], 'status': 'final_native_identity_and_quality_verified',
                         'quality_report': str(quality_path)})
    assert sum(v['status'] == 'final_native_identity_and_quality_verified' for v in outcomes) == summary['joint_passes']
    sha(Path(__file__))
    with output.open('x') as stream:
        json.dump({'status': 'prospective_final_joint_pass_native_identities_verified', 'outcomes': outcomes,
                   'source_sha256': refs, 'research_complete': False,
                   'scope': 'Exact frozen circuit/net/place/RR graph, VPR, route and log hashes for every claimed final joint pass. Complements component capacity/crossing audits; no new routing run or proof of research completion.'}, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
