"""Wait for frozen five-kind RTL and synthesis, then run four RTL and native gates.

One submission owner, no retries or timing adoption. Any failed gate stops for review.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from audit_full_color_outputs import audit


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(package):
    manifest = json.loads((package / 'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        assert sha(package / name) == digest, name


def rtl_gate(package, transactions):
    receipt = json.loads((package / 'rtl_attempt_01_terminal_audit.json').read_text())
    assert receipt['returncode'] == 0 and receipt['functional_gate_pass'], package
    assert receipt['completed_transactions'] == transactions
    assert receipt['output_comparisons'] == transactions * 30
    assert receipt['full_expected_outputs_equal']
    log = package / 'rtl_attempt_01.log'
    assert sha(log) == receipt['log_sha256']
    verify(package)
    text = log.read_text()
    assert 'Starting C post checking' in text
    assert '*** C/RTL co-simulation finished: PASS ***' in text
    independent = audit(package, transactions, log)
    assert independent['full_expected_outputs_equal']
    assert independent['completed_transactions'] == transactions
    assert len(independent['ports']) == 30 * transactions
    (package / 'queue_independent_outputs_audit.json').write_text(
        json.dumps(independent, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('queue', type=Path)
    args = parser.parse_args()
    queue = args.queue.resolve()
    lock = (queue / 'owner.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not (queue / 'state.json').exists(), 'Queue already started'
    config = json.loads((queue / 'manifest.json').read_text())
    five, four, cohort = (Path(config[k]) for k in ('five', 'four', 'cohort'))
    tools = Path(__file__).resolve().parent
    for name, digest in config['tool_hashes'].items():
        assert sha(Path(name)) == digest
    for package, digest in config['package_manifests'].items():
        assert sha(Path(package) / 'manifest.json') == digest
    state = {'status': 'waiting_prerequisites', 'manifest_sha256': sha(queue / 'manifest.json')}

    def save(**values):
        state.update(values, observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        tmp = queue / 'state.json.tmp'
        tmp.write_text(json.dumps(state, indent=2) + '\n')
        tmp.replace(queue / 'state.json')

    def run(command, name):
        with (queue / (name + '.log')).open('x') as log:
            process = subprocess.Popen(command, cwd=tools.parent, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            save(status=name, command=command, job_pid=process.pid)
            while True:
                try:
                    rc = process.wait(timeout=60)
                    break
                except subprocess.TimeoutExpired:
                    save()
            save(last_returncode=rc)
            assert rc == 0, (name, rc)

    try:
        while True:
            five_ready = (five / 'rtl_attempt_01_terminal_audit.json').exists()
            synth_ready = (four / 'synthesis_terminal.json').exists()
            if five_ready:
                receipt = json.loads((five / 'rtl_attempt_01_terminal_audit.json').read_text())
                assert receipt['functional_gate_pass'] and receipt['returncode'] == 0
            if synth_ready:
                receipt = json.loads((four / 'synthesis_terminal.json').read_text())
                assert receipt['synthesis_gate_pass'] and receipt['returncode'] == 0
            save(five_terminal_present=five_ready, four_synthesis_terminal_present=synth_ready)
            if five_ready and synth_ready:
                break
            time.sleep(60)
        rtl_gate(five, 5)
        verify(four)
        assert not (four / 'rtl_attempt_01_supervision.json').exists(), 'Four RTL already started'
        run([sys.executable, str(tools / 'supervise_cosim_attempt.py'), str(four),
             '--attempt', 'rtl_attempt_01', '--tcl', 'cosim.tcl', '--transactions', '4'], 'four_rtl')
        rtl_gate(four, 4)
        assert not (cohort / 'summary.json').exists(), 'Native cohort already started'
        run([sys.executable, str(cohort / 'launch.py')], 'native_cohort')
        run([sys.executable, str(cohort / 'audit_batch.py')], 'native_differential_audit')
        run([sys.executable, str(tools / 'audit_native_input_identity.py'),
             str(cohort / 'manifest.json'), '--output', str(cohort / 'input_identity_final_audit.json')],
            'native_input_identity_audit')
        receipt = json.loads((cohort / 'final_audit.json').read_text())
        identity = json.loads((cohort / 'input_identity_final_audit.json').read_text())
        assert receipt['status'] == 'pass' and len(receipt['verified_cases']) == 9
        assert receipt['verified_native_trials'] == 202 and receipt['checked_color_calls'] == 88
        assert identity['all_expected_input_maps_equal'] and not identity['pending_cases']
        assert identity['unique_frozen_inputs_verified'] == 129
        save(status='correctness_chain_pass_awaiting_primary_timing_review')
        return 0
    except Exception as error:
        save(status='stopped_for_primary_review', error=repr(error))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
