"""Independently replay one completed prospective sweep/refresh case."""
from pathlib import Path
import argparse
import hashlib
import json
import time
import audit_adaptive_compound_sweep_stage as sweep
import audit_compound_repeat_refresh_stage as refresh


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cohort', type=Path)
    parser.add_argument('label')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    cohort = args.cohort.resolve()
    output = args.output.resolve()
    raw = (cohort / 'manifest.json').read_bytes()
    state = json.loads(raw)
    result = next(row for row in state['cases'] if row['label'] == args.label)
    assert result['status'] == 'initial_sweep_refresh_terminal_requires_independent_review'
    assert [s['stage'] for s in result['stages']] == ['sweep', 'refresh']
    assert all(s['status'] == 'terminal' for s in result['stages'])
    producer = cohort / args.label
    protocol = json.loads((producer / 'protocol.json').read_text())
    assert len(protocol['cases']) == 1 and protocol['cases'][0]['label'] == args.label
    output.mkdir()
    (output / 'producer_snapshot.json').write_bytes(raw)
    started = time.monotonic_ns()
    reviews = []
    for name, module in [('sweep', sweep), ('refresh', refresh)]:
        view = output / name
        view.mkdir()
        adapted = json.loads(json.dumps(protocol))
        if name == 'refresh':
            adapted['cases'][0]['policy_parent_tree'] = json.loads((producer / 'sweep' / args.label / 'manifest.json').read_text())['current_tree']
        (view / 'protocol.json').write_text(json.dumps(adapted, indent=2) + '\n')
        (view / 'launch_protocol.json').write_text(json.dumps({'source_sha256': {}}) + '\n')
        # This is an existing auditor ABI tag, not a claim that three cases ran.
        (view / 'manifest.json').write_text(json.dumps({'status': 'three_case_single_sweeps_complete_requires_independent_review',
                                                       'declared_cases': 1, 'scope': 'One-case adapter for frozen auditor ABI.'}) + '\n')
        (view / args.label).symlink_to(producer / name / args.label, target_is_directory=True)
        module.P = view
        module.main()
        audit = json.loads((view / 'independent_audit.json').read_text())
        assert len(audit['outcomes']) == 1
        reviews.append(view / 'independent_audit.json')
    refs = {}

    def sha(path):
        path = Path(path)
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                digest.update(block)
        refs[str(path)] = digest.hexdigest()
        return refs[str(path)]

    case = protocol['cases'][0]
    final_tree = Path(result['final_tree'])
    quality_path = final_tree.parent / 'native_validation/validation.json'
    quality = json.loads(quality_path.read_text())
    assert quality == result['quality']
    assert quality['legal'] and quality['vpr_exit_status'] == 0
    native = Path(case['native_case'])
    for key, name in [('arch', 'architecture.xml'), ('circuit', 'circuit.blif'),
                      ('net', 'circuit.net'), ('place', 'circuit.place'), ('rr_graph', 'rr_graph.xml')]:
        assert sha(native / name) == quality['inputs'][key + '_sha256']
    native_command = quality['command']
    final_native_route = quality_path.parent / native_command[native_command.index('--route_file') + 1]
    assert sha(final_native_route) == quality['inputs']['route_sha256']
    assert sha(protocol['vpr']) == quality['inputs']['vpr_sha256']
    for key, name in [('stdout', 'vpr_analysis.stdout'), ('stderr', 'vpr_analysis.stderr')]:
        assert sha(quality_path.parent / name) == quality[key + '_sha256']
    baseline_crossings = json.loads((producer / 'sweep' / args.label / 'manifest.json').read_text())['baseline_crossings']
    checks = {'native_legal': quality['legal'],
              'wirelength': quality['total_wirelength'] <= case['baseline_wirelength'],
              'CPD': quality['critical_path_delay_ns'] <= case['baseline_cpd_ns'],
              'modeled_transitions': result['crossings'] <= baseline_crossings}
    for path in [producer / 'protocol.json', output / 'producer_snapshot.json', final_tree, quality_path,
                 *reviews, Path(__file__).resolve(), Path(sweep.__file__), Path(refresh.__file__)]:
        sha(path)
    report = {'status': 'prospective_initial_case_decisions_and_native_provenance_reviewed',
              'label': args.label, 'checks': checks, 'joint_quality_pass': all(checks.values()),
              'quality': quality, 'crossings': result['crossings'], 'baseline_crossings': baseline_crossings,
              'final_tree': str(final_tree), 'final_native_route': str(final_native_route),
              'refinement_wall_ns': result['wall_ns'],
              'audit_wall_ns': time.monotonic_ns() - started, 'source_sha256': refs,
              'scope': 'One declared prospective case; frozen auditors replay recorded selection/budgets/native decisions and final graph/tree/capacity. Native final input/report hashes joined independently. No optimal-search proof, independent full execution repeat, pipeline acceleration or board claim.',
              'research_complete': False}
    (output / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'label': args.label, 'checks': checks}))


if __name__ == '__main__':
    main()
