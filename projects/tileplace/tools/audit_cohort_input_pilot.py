#!/usr/bin/env python3
"""Audit a completed fresh native baseline/input/refinement integration pilot."""
import argparse
import json
from pathlib import Path
from audit_fixed_development import audit_native_trials
from run_fixed_development import validate
from run_tileplace_v2 import timing_report_for_closure
from tileplace_provenance import verify_files
from tileplace_vpr import ContractError, dump_json, sha256


def audit(root, baseline_path, implementation):
    process = json.loads((root / 'refinement/process.json').read_text())
    if process['returncode'] != 0:
        raise ContractError('pilot refinement failed')
    baseline = json.loads(baseline_path.read_text())
    verify_files(list(baseline['outputs'].values()))
    verify_files(baseline['inputs'])
    timing_report_for_closure(baseline)
    report_path = root / 'refinement/report.json'
    report = validate(report_path, implementation)
    for key in ('cpd_ns', 'wirelength', 'legal', 'status'):
        if report['baseline'][key] != baseline[key]:
            raise ContractError('search baseline differs from native baseline')
    count = audit_native_trials(report)
    manifest_path = root / 'contract/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    verify_files(list(manifest['inputs'].values()))
    mapping = manifest['connection_endpoint_mapping']
    expected = mapping['connections']
    if not expected or any(mapping[key] != expected for key in
                           ('mapped_sources', 'mapped_sinks', 'atom_timing_pin_mapped', 'timed_fully_mapped')):
        raise ContractError('incomplete connection mapping')
    result = {'schema': 'TILEPLACE_FRESH_INPUT_PILOT_AUDIT_V1', 'status': 'pass',
              'implementation_sha256': implementation, 'verified_native_trials': count,
              'connections': expected, 'baseline': report['baseline'], 'final': report['final'],
              'process': process, 'files': [{'path': str(path.resolve()), 'sha256': sha256(path)}
                  for path in (baseline_path, manifest_path, report_path)],
              'scope': 'Observed diffeq integration pilot only; not prospective cohort evidence'}
    dump_json(root / 'refinement_audit.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--implementation', required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.root.resolve(), args.baseline.resolve(), args.implementation)))
