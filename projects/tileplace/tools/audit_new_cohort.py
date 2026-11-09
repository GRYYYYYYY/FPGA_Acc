#!/usr/bin/env python3
"""Independently audit a prospective cohort, including its failure denominator."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from audit_fixed_development import audit_native_trials
from run_fixed_development import validate
from run_v4_timing_protocol import signature, feedback_signature
from tileplace_provenance import verify_files
from tileplace_vpr import ContractError, dump_json, sha256


def audit(protocol_path, seal, partial=False):
    if sha256(protocol_path) != seal:
        raise ContractError('protocol seal mismatch')
    protocol = json.loads(protocol_path.read_text())
    verify_files(protocol['files'])
    root = Path(protocol['output_root'])
    matrix_path = root / ('progress.json' if partial else 'summary.json')
    matrix_bytes = matrix_path.read_bytes()
    matrix = json.loads(matrix_bytes)
    if matrix['protocol_sha256'] != seal:
        raise ContractError('matrix protocol mismatch')
    rows = matrix['cases']
    expected = protocol['cases']
    if [r['design'] for r in rows] != [c['design'] for c in expected[:len(rows)]]:
        raise ContractError('case order or membership differs from protocol')
    if len(rows) > len(expected) or (not partial and len(rows) != len(expected)):
        raise ContractError('case denominator incomplete')
    checked = []
    ratios = []
    for row, planned in zip(rows, expected):
        stages = planned['stages'] + planned['refinements']
        for receipt, stage in zip(row['stages'], planned['stages']):
            if receipt['name'] != stage['name'] or receipt['returncode'] != 0:
                raise ContractError('completed stage receipt mismatch')
            path = Path(stage['cwd']) / (stage['name'] + '.command.json')
            if json.loads(path.read_text()) != stage['command']:
                raise ContractError('executed command differs from protocol')
            process_path = Path(stage['cwd']) / ('process.json' if stage['name'] == 'baseline'
                                                else stage['name'] + '.process.json')
            actual = json.loads(process_path.read_text())
            if actual['returncode'] != 0 or actual['elapsed_s'] != receipt['elapsed_s']:
                raise ContractError('stage process receipt mismatch')
            if stage['name'] == 'paths':
                metrics = json.loads((Path(stage['cwd']) / 'paths.stdout.log').read_text())
                if (metrics.get('legal') is not True or metrics['tasks'] != metrics['routed_tasks']
                        or metrics['overused_resources'] != 0):
                    raise ContractError('invalid completed CPU paths')
        if row['status'] == 'fail':
            stage = next(s for s in stages if s['name'] == row['failed_stage'])
            folder = Path(stage['cwd'])
            name = 'process.json' if stage['name'] == 'baseline' else stage['name'] + '.process.json'
            process_path = folder / name
            command_path = folder / (stage['name'] + '.command.json')
            if not process_path.is_file() or json.loads(command_path.read_text()) != stage['command']:
                raise ContractError('failed stage evidence missing')
            logs = [folder / name for name in (('stdout.log', 'stderr.log') if stage['name'] == 'baseline'
                    else (stage['name'] + '.stdout.log', stage['name'] + '.stderr.log'))]
            retained_native_trials = 0
            for receipt in row['repeats']:
                report_path = Path(receipt['path'])
                if sha256(report_path) != receipt['sha256']:
                    raise ContractError('retained repeat report changed')
                report = validate(report_path, protocol['implementation_sha256'])
                retained_native_trials += audit_native_trials(report)
            checked.append({'design': row['design'], 'status': 'fail', 'error': row['error'],
                            'failed_stage': row['failed_stage'], 'process': json.loads(process_path.read_text()),
                            'process_sha256': sha256(process_path),
                            'retained_native_trials': retained_native_trials,
                            'logs': [{'path': str(p), 'sha256': sha256(p)} for p in logs]})
            continue
        if row['status'] != 'pass' or len(row['stages']) != len(planned['stages']):
            raise ContractError('successful case input stages incomplete')
        if len(row['repeats']) != protocol['repetitions']:
            raise ContractError('repeat count mismatch')
        contract_stage = next(s for s in planned['stages'] if s['name'] == 'contract')
        contract_path = Path(contract_stage['command'][contract_stage['command'].index('--output') + 1]) / 'manifest.json'
        contract = json.loads(contract_path.read_text())
        verify_files(list(contract['inputs'].values()))
        mapping = contract['connection_endpoint_mapping']
        expected_connections = mapping['connections']
        if not expected_connections or mapping['atom_timing_pin_unmapped'] != 0 or any(
                mapping[key] != expected_connections for key in
                ('mapped_sources', 'mapped_sinks', 'atom_timing_pin_mapped', 'timed_fully_mapped')):
            raise ContractError('incomplete successful-case contract mapping')
        baseline_path = Path(planned['stages'][0]['cwd']) / 'baseline.json'
        baseline = json.loads(baseline_path.read_text())
        verify_files(baseline['inputs'])
        verify_files(list(baseline['outputs'].values()))
        reports = []
        count = 0
        for receipt, stage in zip(row['repeats'], planned['refinements']):
            path = Path(stage['cwd']) / 'report.json'
            if str(path) != receipt['path'] or sha256(path) != receipt['sha256']:
                raise ContractError('repeat report receipt mismatch')
            command_path = Path(stage['cwd']) / (stage['name'] + '.command.json')
            if json.loads(command_path.read_text()) != stage['command']:
                raise ContractError('refinement command differs from protocol')
            process_path = Path(stage['cwd']) / (stage['name'] + '.process.json')
            actual = json.loads(process_path.read_text())
            if actual != receipt['process'] or actual['returncode'] != 0:
                raise ContractError('refinement process receipt mismatch')
            report = validate(path, protocol['implementation_sha256'])
            for key in ('cpd_ns', 'wirelength', 'legal', 'status'):
                if report['baseline'][key] != baseline[key]:
                    raise ContractError('native baseline mismatch')
            native_count = audit_native_trials(report)
            if native_count != receipt['verified_native_trials']:
                raise ContractError('native trial count mismatch')
            count += native_count
            reports.append(report)
        identities = [(signature(r), feedback_signature(r), r['phases'],
                       [t['transactions'] for t in r['trials']]) for r in reports]
        if any(x != identities[0] for x in identities[1:]):
            raise ContractError('repeat trajectory mismatch')
        first = reports[0]
        cpd = first['final']['cpd_ns'] / baseline['cpd_ns']
        wl = first['final']['wirelength'] / baseline['wirelength']
        if cpd != row['cpd_ratio'] or wl != row['wirelength_ratio'] or first['final'] != row['final']:
            raise ContractError('matrix metrics differ from reports')
        ratios.append((cpd, wl))
        checked.append({'design': row['design'], 'status': 'pass', 'verified_native_trials': count,
                        'cpd_change_pct': (cpd - 1) * 100, 'wirelength_change_pct': (wl - 1) * 100,
                        'repeats_exact': True})
    result = {'schema': 'TILEPLACE_NEW_COHORT_AUDIT_V1', 'status': 'partial' if partial else 'pass',
              'protocol_sha256': seal, 'matrix_sha256': hashlib.sha256(matrix_bytes).hexdigest(), 'expected_cases': len(expected),
              'completed_cases': len(rows), 'successful_cases': len(ratios), 'cases': checked,
              'scope': 'Successful subset metrics; all failures retained in denominator. ' + protocol['scope']}
    if ratios:
        result['successful_subset_geomean_change_pct'] = {
            key: (math.exp(sum(math.log(r[i]) for r in ratios) / len(ratios)) - 1) * 100
            for i, key in enumerate(('cpd', 'wirelength'))}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--partial', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.protocol.resolve(), args.sha256, args.partial)
    dump_json(args.output, result)
    print(json.dumps(result))
