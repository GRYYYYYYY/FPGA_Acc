"""Advance the frozen input-union validation plan after complete upstream gates.

Single submission owner; no recovery, source edits, optimization, or goal completion.
"""
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from audit_full_color_outputs import audit


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(pid):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return fields[19] if fields[0] != 'Z' else None
    except FileNotFoundError:
        return None


def verify_sources(package, expected_manifest):
    manifest_path = package / 'manifest.json'
    assert digest(manifest_path) == expected_manifest, manifest_path
    manifest = json.loads(manifest_path.read_text())
    for name, expected in manifest['files'].items():
        assert digest(package / name) == expected, name


def verify_gate(package, attempt, transactions, expected_manifest):
    receipt_path = package / (attempt + '_terminal_audit.json')
    receipt = json.loads(receipt_path.read_text())
    assert receipt['functional_gate_pass'] and receipt['returncode'] == 0, receipt_path
    assert receipt['completed_transactions'] == transactions, receipt_path
    assert receipt['output_comparisons'] == 30 * transactions, receipt_path
    assert receipt['full_expected_outputs_equal'], receipt_path
    log_path = package / (attempt + '.log')
    assert Path(receipt['log']) == log_path
    assert digest(log_path) == receipt['log_sha256'], log_path
    assert '*** C/RTL co-simulation finished: PASS ***' in log_path.read_text()
    assert 'Starting C post checking' in log_path.read_text()
    verify_sources(package, expected_manifest)
    # Independently re-read all typed frames; do not rely on the receipt's bool.
    output = audit(package, transactions, log_path)
    assert output['full_expected_outputs_equal'] and len(output['ports']) == transactions * 30
    assert all(row['elements'] > 0 and row['mismatches'] == 0 for row in output['ports'])
    return {'terminal_receipt': str(receipt_path), 'terminal_sha256': digest(receipt_path),
            'log_sha256': digest(log_path), 'typed_comparisons': len(output['ports'])}


def main(root):
    root = root.resolve()
    manifest = json.loads((root / 'manifest.json').read_text())
    lock = (root / 'chain.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not (root / 'state.json').exists(), 'Existing chain must be reconciled, not overwritten'
    for name, expected in manifest['tools'].items():
        assert digest(Path(name)) == expected, name
    state = {'started_at_utc': utc(), 'chain_pid': os.getpid(),
             'status': 'waiting_four_transaction_gate', 'completed': [],
             'scope': 'frozen correctness chain only; larger research goal remains incomplete'}

    def save(**updates):
        state.update(updates, observed_at_utc=utc())
        temporary = root / 'state.json.tmp'
        temporary.write_text(json.dumps(state, indent=2) + '\n')
        temporary.replace(root / 'state.json')

    def child(command, log_path, status):
        for name, expected in manifest['tools'].items():
            assert digest(Path(name)) == expected, name
        with log_path.open('x') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                       stdin=subprocess.DEVNULL, start_new_session=True)
            save(status=status, child_pid=process.pid, child_command=command)
            result = process.wait()
        assert result == 0, {'command': command, 'returncode': result, 'log': str(log_path)}
        save(child_pid=None, child_returncode=result)

    save()
    try:
        four = Path(manifest['four_package'])
        terminal = four / 'recovery_attempt_03_terminal_audit.json'
        original_pid = manifest['four_supervisor_pid']
        while not terminal.exists():
            assert fingerprint(original_pid) == manifest['four_supervisor_starttime'], \
                'Upstream supervisor absent without terminal receipt; primary must reconcile'
            save()
            time.sleep(60)
        gate = verify_gate(four, 'recovery_attempt_03', 4, manifest['four_manifest_sha256'])
        state['completed'].append({'stage': 'four_transaction_rtl', 'evidence': gate})
        five = Path(manifest['five_package'])
        verify_sources(five, manifest['five_manifest_sha256'])
        assert not (five / 'run_attempt_01.log').exists()
        supervisor = manifest['cosim_supervisor']
        command = [sys.executable, supervisor, str(five), '--attempt', 'run_attempt_01',
                   '--tcl', 'run.tcl', '--transactions', '5']
        child(command, root / 'five_supervisor.log', 'running_five_kind_rtl')
        gate = verify_gate(five, 'run_attempt_01', 5, manifest['five_manifest_sha256'])
        # Verify complete identities against the independent Python fixtures in
        # the terminal C postcheck's output, in addition to full typed pools.
        stage = Path(manifest['native_stage'])
        verify_sources(stage, manifest['native_stage_manifest_sha256'])
        parser_path = stage / 'cpp_snapshot/compare_proposals.py'
        sys.path.insert(0, str(parser_path.parent))
        spec = importlib.util.spec_from_file_location('identity_parser', parser_path)
        parser = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(parser)
        fixtures = Path(manifest['fixtures'])
        assert digest(fixtures / 'manifest.json') == manifest['fixtures_manifest_sha256']
        fixture_manifest = json.loads((fixtures / 'manifest.json').read_text())
        postcheck = (five / 'run_attempt_01.log').read_text().split('Starting C post checking', 1)[1]
        for kind in ['move', 'swap', 'macro_swap', 'chain2', 'chain3']:
            for name, expected in fixture_manifest['fixtures'][kind]['files'].items():
                assert digest(fixtures / kind / name) == expected
            sections = re.findall(r'BEGIN ' + kind + r'\n(.*?)END ' + kind + r'\n', postcheck, re.S)
            assert len(sections) == 1, kind
            assert parser.parse(sections[0]) == parser.parse((fixtures / kind / 'expected.txt').read_text()), kind
        gate['complete_identity_cases'] = 5
        state['completed'].append({'stage': 'five_kind_rtl', 'evidence': gate})
        native = Path(manifest['native_cohort'])
        assert digest(native / 'manifest.json') == manifest['native_cohort_manifest_sha256']
        stage = Path(manifest['native_stage'])
        verify_sources(stage, manifest['native_stage_manifest_sha256'])
        assert not (native / 'summary.json').exists()
        child([sys.executable, str(native / 'launch.py')], root / 'native_batch.log', 'running_nine_case_native')
        child([sys.executable, str(native / 'audit_batch.py')], root / 'native_final_audit.log', 'auditing_nine_case_native')
        final = json.loads((native / 'final_audit.json').read_text())
        assert final['status'] == 'pass' and len(final['verified_cases']) == 9
        state['completed'].append({'stage': 'nine_case_native', 'evidence': {
            'path': str(native / 'final_audit.json'), 'sha256': digest(native / 'final_audit.json')}})
        save(status='validation_chain_pass')
        return 0
    except Exception as error:
        save(status='stopped_for_primary_review', error=repr(error))
        print(json.dumps(state), flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main(Path(sys.argv[1])))
