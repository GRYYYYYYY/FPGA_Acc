#!/usr/bin/env python3
"""Validate and bind artifacts from a completed native VPR baseline command."""
import argparse
import json
from pathlib import Path

from run_vpr_placement_baseline import parse_vpr_metrics
from tileplace_vpr import ContractError, dump_json, sha256


def record(root, design):
    process = json.loads((root / 'process.json').read_text())
    if process['returncode'] != 0:
        raise ContractError('native baseline process failed')
    command = json.loads((root / 'command.json').read_text())
    log = (root / 'stdout.log').read_text()
    for marker in ('Completed placement consistency check successfully.',
                   'Completed routing consistency check successfully.', 'VPR succeeded'):
        if marker not in log:
            raise ContractError('native baseline success marker missing')
    metrics = parse_vpr_metrics(log)
    outputs = {}
    output_names = {
        'netlist': design + '.net', 'place': design + '.place',
        'route': design + '.route', 'rr_graph': 'rr_graph.xml',
        'native_macros': 'place_macros.echo',
        'timing_setup_report': 'report_timing.setup.rpt',
        'stdout': 'stdout.log', 'stderr': 'stderr.log',
        'command': 'command.json', 'process': 'process.json',
    }
    for key, name in output_names.items():
        path = root / name
        if not path.is_file():
            raise ContractError('baseline output missing: ' + name)
        outputs[key] = {'path': str(path.resolve()), 'sha256': sha256(path)}
    # Command prefix is taskset -c CPU followed by VPR, architecture and circuit.
    if command[:2] != ['taskset', '-c'] or len(command) < 6:
        raise ContractError('unsupported baseline command layout')
    inputs = [{'path': str(Path(value).resolve()), 'sha256': sha256(Path(value))}
              for value in command[3:6]]
    result = {'schema': 'TILEPLACE_NEW_COHORT_NATIVE_BASELINE_V1', 'status': 'pass',
              'legal': True, 'returncode': 0, 'cpd_ns': metrics['cpd_ns'],
              'wirelength': metrics['wirelength'], 'metrics': metrics,
              'inputs': inputs, 'outputs': outputs,
              'scope': 'Native baseline only; no refinement outcome'}
    dump_json(root / 'baseline.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--design', required=True)
    args = parser.parse_args()
    result = record(args.root.resolve(), args.design)
    print(json.dumps({key: result[key] for key in ('status', 'cpd_ns', 'wirelength')}))


if __name__ == '__main__':
    main()
