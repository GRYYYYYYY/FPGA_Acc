"""Synthetic contract checks only; creates no experimental observations."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile


def main():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('summary', root / 'tools/audit_prospective_policy_cohort.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix='dieroute_summary_contract_') as temp:
        directory = Path(temp)
        baseline = directory / 'baselines'
        capacity = directory / 'capacity'
        baseline.mkdir()
        capacity.mkdir()

        def write(path, value):
            path.write_text(json.dumps(value))
            return str(path)

        labels = ['apex2_seed' + str(i) for i in range(6, 11)]
        write(baseline / 'independent_audit.json', {'outcomes': [
            {'seed': i, 'native_legal': True, 'wirelength': 100, 'cpd_ns': 10}
            for i in range(6, 11)]})
        write(baseline / 'candidate_policy.json', {})
        write(capacity / 'protocol.json', {'labels': labels})
        evidence = directory / 'evidence.txt'
        evidence.write_text('synthetic')
        refs = {str(evidence): hashlib.sha256(evidence.read_bytes()).hexdigest()}
        cases = []
        initial = 'prospective_initial_case_decisions_and_native_provenance_reviewed'
        mode = 'prospective_native_mode_acceptance_orders_and_native_wirelength_reviewed'
        fallback = 'prospective_capacity_fallback_mixture_capacity_and_native_selection_reviewed'
        leaf = write(directory / 'leaf.json', {'wirelength': 90, 'cpd_ns': 9,
                                              'model_crossings': 2, 'checks': {'native_legal': True, 'capacity': True}})
        for i, label in enumerate(labels):
            report = {'label': label, 'source_sha256': refs}
            if i == 0:
                report.update(status=initial, joint_quality_pass=True, checks={'native_legal': True},
                              quality={'total_wirelength': 90, 'critical_path_delay_ns': 9}, crossings=2)
            elif i == 1:
                report.update(status=mode, final_original_baseline_joint_pass=True, current_state={'audit': leaf})
            elif i in (2, 3):
                report.update(status=fallback, joint_quality_pass=(i == 2), selected_native_audit=leaf if i == 2 else None)
            row = {'label': label, 'status': 'synthetic_terminal', 'mode_status': 'synthetic_mode_terminal',
                   'joint_quality_pass': i < 3}
            if i < 4:
                row['final_report'] = write(directory / (label + '.json'), report)
            write(capacity / (label + '_mode_snapshot.json'), {'label': label, 'status': row['mode_status']})
            cases.append(row)
        state = {'status': 'five_prospective_policy_cases_terminal_require_final_cohort_audit', 'cases': cases}
        write(capacity / 'manifest.json', state)
        result = module.aggregate(baseline, capacity, directory / 'valid.json')
        assert result['joint_passes'] == 3 and result['unresolved'] == 1 and result['retained'] == 5
        assert result['rows'][3]['classification'] == 'verified_policy_quality_failure'

        def rejected(name):
            output = directory / (name + '.json')
            try:
                module.aggregate(baseline, capacity, output)
            except AssertionError:
                assert not output.exists()
                return
            raise AssertionError('Invalid evidence accepted: ' + name)

        evidence.write_text('tampered')
        rejected('tampered_evidence')
        evidence.write_text('synthetic')
        duplicate = copy.deepcopy(state)
        duplicate['cases'][-1] = duplicate['cases'][0]
        write(capacity / 'manifest.json', duplicate)
        rejected('duplicate_case')
        write(capacity / 'manifest.json', state)
        inconsistent = json.loads(Path(cases[0]['final_report']).read_text())
        inconsistent['quality']['critical_path_delay_ns'] = 11
        write(Path(cases[0]['final_report']), inconsistent)
        rejected('false_quality_pass')
    output = Path(sys.argv[1]).resolve()
    report = {'status': 'synthetic_summary_contract_checks_passed',
              'checks': ['all_three_report_types', 'quality_failure_retained', 'upstream_failure_retained',
                         'tamper_rejected', 'duplicate_case_rejected', 'false_quality_pass_rejected'],
              'scope': 'Synthetic interface checks only; zero research observations or native routing runs.',
              'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [Path(__file__).resolve(), root / 'tools/audit_prospective_policy_cohort.py']}}
    with output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(report['status'])


if __name__ == '__main__':
    main()
