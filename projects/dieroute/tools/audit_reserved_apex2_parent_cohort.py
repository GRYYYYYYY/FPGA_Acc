"""Bind the five archived parent reviews to current inputs and native results.

This aggregates existing connectivity/provenance audits; it does not rerun
their algorithms or establish the final refinement cohort's quality.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    evidence = {}
    rows = []

    def read(path):
        evidence[str(path)] = digest(path)
        return json.loads(path.read_text())

    for seed in range(1, 6):
        label = f'apex2_seed{seed}'
        parent = ROOT / 'work/reserved_apex2_parent_20261017/parents' / label
        baseline = ROOT / 'work/reserved_native_baselines_20261017' / label
        review = ROOT / f'work/reserved_apex2_seed{seed}_parent_review' / 'manifest.json'
        # Seed 1's corrected review preserves the earlier successful tree audit.
        review = ROOT / ('work/reserved_apex2_seed1_parent_review_v2_20261017'
                         if seed == 1 else f'work/reserved_apex2_seed{seed}_parent_review_20261017') / 'manifest.json'
        manifest = read(review)
        assert manifest['status'] == 'parent_tree_provenance_writeback_native_validation_terminal'
        assert all(step['returncode'] == 0 for step in manifest['steps'])
        for name, expected in [
            ('tree_audit.json', 'final_native_rr_tree_connectivity_and_resource_memberships_reconstructed'),
            ('session_provenance_audit.json', 'actual_persistent_session_inputs_binary_tasks_and_request_lineage_audited'),
        ]:
            audit = read(parent / name)
            assert audit['status'] == expected
            for filename, expected_hash in audit['source_sha256'].items():
                assert digest(filename) == expected_hash, filename
                evidence[filename] = expected_hash
        route = read(parent / 'route.json')
        assert route['legal'] and route['overused_resources'] == 0
        quality = read(parent / 'native_validation/validation.json')
        assert quality['vpr_exit_status'] == 0
        assert all(quality[k] is True for k in
                   ['legal', 'route_loaded', 'routing_consistency', 'successfully_routed', 'vpr_succeeded'])
        assert quality['channel_width'] == 80
        files = {'arch': baseline / 'architecture.xml', 'circuit': baseline / 'circuit.blif',
                 'net': baseline / 'circuit.net', 'place': baseline / 'circuit.place',
                 'rr_graph': baseline / 'rr_graph.xml', 'route': parent / 'native.route',
                 'vpr': Path(quality['command'][0])}
        for key, path in files.items():
            assert digest(path) == quality['inputs'][key + '_sha256'], str(path)
            evidence[str(path)] = quality['inputs'][key + '_sha256']
        for key, name in [('stdout', 'vpr_analysis.stdout'), ('stderr', 'vpr_analysis.stderr')]:
            path = parent / 'native_validation' / name
            assert digest(path) == quality[key + '_sha256']
            evidence[str(path)] = quality[key + '_sha256']
        rows.append(dict(seed=seed, native_legal=True,
                         wirelength=quality['total_wirelength'], cpd_ns=quality['critical_path_delay_ns'],
                         baseline_wirelength=quality['baseline_wirelength'],
                         baseline_cpd_ns=quality['baseline_cpd_ns'],
                         wl_cpd_nonincrease=(quality['total_wirelength'] <= quality['baseline_wirelength']
                                             and quality['critical_path_delay_ns'] <= quality['baseline_cpd_ns'])))
    evidence[str(Path(__file__).resolve())] = digest(__file__)
    output = ROOT / 'work/reserved_apex2_parent_cohort_review_20261017'
    output.mkdir(exist_ok=False)
    report = dict(status='five_parent_review_chains_and_current_artifact_hashes_verified',
                  cases=rows, source_sha256=evidence, research_complete=False,
                  scope='Aggregates archived tree/provenance audits and native validation with current hash checks. '
                        'No rerun of native STA; no crossing joint gate, final refinement, runtime speedup or physical claim.')
    (output / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(status=report['status'], cases=rows)))


if __name__ == '__main__':
    main()
