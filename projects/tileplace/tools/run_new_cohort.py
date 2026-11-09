#!/usr/bin/env python3
"""Execute a sealed prospective cohort; retain every failure without retries."""
import argparse
import json
import os
import subprocess
import time
from pathlib import Path

from audit_fixed_development import audit_native_trials
from record_native_baseline import record
from run_fixed_development import validate
from run_v4_timing_protocol import signature, feedback_signature
from tileplace_provenance import verify_files
from tileplace_vpr import ContractError, dump_json, sha256


def execute(stage):
    root = Path(stage['cwd'])
    root.mkdir(parents=True, exist_ok=True)
    prefix = root / stage['name']
    dump_json(Path(str(prefix) + '.command.json'), stage['command'])
    if stage['name'] == 'baseline':
        dump_json(root / 'command.json', stage['command'])
    env = {k: v for k, v in os.environ.items() if not k.startswith('PERSISTROUTE_')}
    env.update(stage.get('env', {}))
    start = time.perf_counter()
    stdout = root / 'stdout.log' if stage['name'] == 'baseline' else Path(str(prefix) + '.stdout.log')
    stderr = root / 'stderr.log' if stage['name'] == 'baseline' else Path(str(prefix) + '.stderr.log')
    with stdout.open('x') as out, stderr.open('x') as err:
        process = subprocess.run(stage['command'], cwd=root, env=env, stdout=out, stderr=err)
    receipt = {'returncode': process.returncode, 'elapsed_s': time.perf_counter() - start}
    dump_json(root / 'process.json' if stage['name'] == 'baseline' else Path(str(prefix) + '.process.json'), receipt)
    if process.returncode:
        raise ContractError(f"stage failed: {stage['name']} exit {process.returncode}")
    if stage['name'] == 'paths':
        metrics = json.loads(stdout.read_text().strip())
        if (metrics.get('legal') is not True or metrics['tasks'] != metrics['routed_tasks']
                or metrics['overused_resources'] != 0):
            raise ContractError('CPU paths incomplete or resources overused')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    if sha256(args.protocol) != args.sha256:
        raise ContractError('protocol seal mismatch')
    protocol = json.loads(args.protocol.read_text())
    verify_files(protocol['files'])
    root = Path(protocol['output_root'])
    root.mkdir(parents=True, exist_ok=False)
    results = []
    for case in protocol['cases']:
        row = {'design': case['design'], 'status': 'running', 'stages': [], 'repeats': []}
        start = time.perf_counter()
        print('START ' + case['design'], flush=True)
        verify_files(protocol['files'])
        try:
            for stage in case['stages']:
                row['stages'].append({'name': stage['name'], **execute(stage)})
                if stage['name'] == 'baseline':
                    record(Path(stage['cwd']), case['design'])
            reports = []
            for stage in case['refinements']:
                process = execute(stage)
                report_path = Path(stage['cwd']) / 'report.json'
                report = validate(report_path, protocol['implementation_sha256'])
                count = audit_native_trials(report)
                reports.append(report)
                row['repeats'].append({'path': str(report_path), 'sha256': sha256(report_path),
                                       'verified_native_trials': count, 'process': process})
            first = reports[0]
            for other in reports[1:]:
                if (signature(first), feedback_signature(first), first['phases'],
                    [t['transactions'] for t in first['trials']]) != (
                    signature(other), feedback_signature(other), other['phases'],
                    [t['transactions'] for t in other['trials']]):
                    raise ContractError('repeat trajectory mismatch')
            row.update(status='pass', baseline=first['baseline'], final=first['final'],
                       cpd_ratio=first['final']['cpd_ns'] / first['baseline']['cpd_ns'],
                       wirelength_ratio=first['final']['wirelength'] / first['baseline']['wirelength'])
        except Exception as error:
            row.update(status='fail', error=str(error), failed_stage=stage['name'])
        row['end_to_end_s'] = time.perf_counter() - start
        results.append(row)
        dump_json(root / 'progress.json', {'protocol_sha256': args.sha256, 'cases': results})
        print('DONE ' + case['design'] + ' ' + row['status'], flush=True)
    verify_files(protocol['files'])
    summary = {'schema': 'TILEPLACE_NEW_COHORT_MATRIX_V1', 'protocol_sha256': args.sha256,
               'cases': results, 'expected_cases': len(protocol['cases']),
               'successful_cases': sum(r['status'] == 'pass' for r in results),
               'scope': protocol['scope']}
    dump_json(root / 'summary.json', summary)


if __name__ == '__main__':
    main()
