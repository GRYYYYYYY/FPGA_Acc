"""Bind the four fixed arithmetic cases to completed evidence and physical audits."""
import json
import shutil
from pathlib import Path
from pre_route_endpoints import sha


def main():
    base = Path('experiments')
    bindings, rows = {}, []

    def load(path):
        bindings[str(path)] = sha(path)
        return json.loads(path.read_text())

    for design in ('adder_tree_2L_032bits', 'adder_tree_2L_128bits',
                   'adder_tree_3L_032bits', 'adder_tree_3L_128bits'):
        trial = (base / 'native_pressure_paired_cached_cost_2026-10-06'
                 if design == 'adder_tree_2L_032bits' else
                 base / 'native_pressure_paired_cached_cohort_2026-10-06' / design)
        receipt = load(trial / 'receipt.json')
        evidence = base / 'native_pressure_paired_evidence_verification_2026-10-06' / design
        er, report = load(evidence / 'receipt.json'), load(evidence / 'report.json')
        assert er['report_sha256'] == sha(evidence / 'report.json')
        assert report['all_evidence_checks_pass'] and er['all_evidence_checks_pass']
        assert report['trial_receipt_sha256'] == sha(trial / 'receipt.json')
        for path, digest in report['input_sha256'].items():
            assert sha(path) == digest
            bindings[path] = digest
        audit = base / 'native_pressure_paired_route_audit_2026-10-06' / design
        ar, ap = load(audit / 'receipt.json'), load(audit / 'protocol.json')
        assert ar['all_pass'] and ar['protocol_sha256'] == sha(audit / 'protocol.json')
        assert ap['trial_receipt_sha256'] == sha(trial / 'receipt.json')
        for item in ar['results']:
            physical = audit / (item['mode'] + '_physical_branches.json')
            assert sha(physical) == item['physical_branches_sha256']
            bindings[str(physical)] = sha(physical)
            assert item['overflow_units'] == 0 and item['full_cohort_exact']
            assert {v['route_sha256'] for v in receipt['results'] if v['mode'] == item['mode']} == {item['route_sha256']}
        groups = {mode: [v for v in receipt['results'] if v['mode'] == mode] for mode in ('off', 'on')}
        means = {mode: sum(v['cached_pipeline_s'] for v in group) / len(group) for mode, group in groups.items()}
        assert means == receipt['mean_cached_pipeline_s']
        qor = {}
        for mode, group in groups.items():
            assert len(group) == 4
            assert len({(v['cpd_ns'], v['wirelength']) for v in group}) == 1
            qor[mode] = {key: group[0][key] for key in ('cpd_ns', 'wirelength')}
        rows.append({'design': design, 'mean_cached_pipeline_s': means,
                     'on_over_off': means['on'] / means['off'], 'qor': qor,
                     'cycles': report['cycles'], 'connections': ar['results'][0]['connections']})
    assert all(sha(path) == digest for path, digest in bindings.items())
    out = base / 'native_pressure_four_case_summary_2026-10-06'
    out.mkdir()
    shutil.copyfile(__file__, out / 'source.py')
    report = {'cases': rows, 'input_sha256': bindings, 'source_sha256': sha(__file__),
              'all_four_cached_on_slower': all(v['on_over_off'] > 1 for v in rows),
              'family_count': 1, 'unseen_family_claim': False,
              'scope': 'Fixed coefficient1 full fresh prediction feedback, two ABBA cycles per case, concurrent host load; excludes initial packing/placement/endpoints/CSR construction. No incremental, cold, hardware or general-model conclusion.'}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (out / 'receipt.json').write_text(json.dumps({'report_sha256': sha(out / 'report.json'), 'all_pass': True}, indent=2) + '\n')
    print(json.dumps(rows), flush=True)


if __name__ == '__main__':
    main()
