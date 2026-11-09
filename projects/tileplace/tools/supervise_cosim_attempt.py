"""Run one authorized cosim attempt with durable progress, exit, and output audits.

No automatic retry or downstream submission. The caller must archive old simulation
vectors and establish that no prior Vitis/XSim job is live before invoking this tool.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from audit_full_color_outputs import audit


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def binding(package):
    path = package / 'manifest.json'
    manifest = json.loads(path.read_text())
    bad = [name for name, digest in manifest['files'].items()
           if not (package / name).is_file()
           or hashlib.sha256((package / name).read_bytes()).hexdigest() != digest]
    return {'files': len(manifest['files']), 'mismatches': bad,
            'manifest_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--attempt', required=True)
    parser.add_argument('--tcl', required=True)
    parser.add_argument('--transactions', required=True, type=int)
    args = parser.parse_args()
    package = args.package.resolve()
    assert re.fullmatch(r'[A-Za-z0-9_]+', args.attempt)
    log_path = package / (args.attempt + '.log')
    receipt_path = package / (args.attempt + '_supervision.json')
    terminal_path = package / (args.attempt + '_terminal_audit.json')
    outputs_path = package / (args.attempt + '_outputs_audit.json')
    settings = '/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis/2022.2/settings64.sh'
    tcl = (package / args.tcl).resolve()
    assert tcl.is_file()
    lock = (package / 'cosim_supervision.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    initial_binding = binding(package)
    assert not initial_binding['mismatches'], initial_binding
    with log_path.open('x') as log:
        command = ['bash', '-c', 'source "$1"\nexec vitis_hls -f "$2"',
                   'cosim-attempt', settings, str(tcl)]
        process = subprocess.Popen(command, cwd=package, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        base = {'started_at_utc': utc(), 'supervisor_pid': os.getpid(),
                'job_pid': process.pid, 'command': command, 'working_directory': str(package),
                'log': str(log_path), 'expected_transactions': args.transactions,
                'source_binding_at_launch': initial_binding,
                'tcl_sha256': hashlib.sha256(tcl.read_bytes()).hexdigest(),
                'scope': 'one authorized attempt; no retries; full typed outputs; no board claims'}
        previous = -1
        output = None
        while True:
            returncode = process.poll()
            text = log_path.read_text(errors='replace')
            completed = max([int(x) for x in re.findall(r'RTL Simulation : (\d+) /', text)], default=0)
            error = None
            if completed > 0 and (completed != previous or returncode is not None):
                try:
                    output = audit(package, args.transactions, log_path)
                    save(outputs_path, output)
                    previous = completed
                except Exception as exception:
                    error = repr(exception)
            state = dict(base, observed_at_utc=utc(), returncode=returncode,
                         process_alive=returncode is None, completed_transactions=completed,
                         output_comparisons=len(output['ports']) if output else 0,
                         full_expected_outputs_equal=bool(output and output['full_expected_outputs_equal']),
                         audit_error=error)
            save(receipt_path, state)
            if returncode is not None:
                final_binding = binding(package)
                state.update(source_binding_at_terminal=final_binding,
                             terminal_cosim_pass='*** C/RTL co-simulation finished: PASS ***' in text,
                             terminal_c_postcheck_started='Starting C post checking' in text,
                             log_sha256=hashlib.sha256(log_path.read_bytes()).hexdigest())
                state['functional_gate_pass'] = bool(returncode == 0
                    and state['terminal_cosim_pass'] and state['terminal_c_postcheck_started']
                    and state['full_expected_outputs_equal'] and not error
                    and output['completed_transactions'] == args.transactions
                    and state['output_comparisons'] == 30 * args.transactions
                    and not final_binding['mismatches']
                    and final_binding['manifest_sha256'] == initial_binding['manifest_sha256'])
                save(terminal_path, state)
                print(json.dumps(state), flush=True)
                return 0 if state['functional_gate_pass'] else 1
            time.sleep(60)


if __name__ == '__main__':
    raise SystemExit(main())
