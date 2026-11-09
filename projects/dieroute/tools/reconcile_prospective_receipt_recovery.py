"""Append an explicit reviewed-recovery aggregate, preserving original failures."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


def main():
    directory = Path(sys.argv[1]).resolve()
    protocol = json.loads((directory / 'protocol.json').read_text())
    assert not (directory / 'manifest.json').exists()
    state = {'status': 'waiting_for_original_capacity_terminal', 'pid': os.getpid(), 'research_complete': False}

    def write(path, value):
        with path.open('x') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')

    def save():
        temp = directory / 'manifest.tmp'
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(directory / 'manifest.json')

    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    try:
        for name, expected in protocol['source_sha256'].items():
            assert sha(name) == expected, name
        save()
        capacity = Path(protocol['capacity'])
        while True:
            original = json.loads((capacity / 'manifest.json').read_text())
            if original['status'] == 'five_prospective_policy_cases_terminal_require_final_cohort_audit':
                break
            assert original['status'] != 'capacity_fallback_queue_stopped_requires_review'
            owner = protocol['owner']
            text = (Path('/proc') / str(owner['pid']) / 'stat').read_text()
            fields = text[text.rfind(')') + 2:].split()
            assert fields[0] != 'Z' and fields[19] == owner['start_ticks']
            time.sleep(10)
        state['status'] = 'reconciling_explicit_receipt_recoveries'
        save()
        view = directory / 'immutable_reconciled_view'
        view.mkdir()
        view_protocol = json.loads((capacity / 'protocol.json').read_text())
        adjusted = copy.deepcopy(original)
        changes = []
        refs = {str(capacity / 'manifest.json'): sha(capacity / 'manifest.json'),
                str(capacity / 'protocol.json'): sha(capacity / 'protocol.json')}
        for row in original['cases']:
            source = capacity / (row['label'] + '_mode_snapshot.json')
            (view / source.name).write_bytes(source.read_bytes())
            refs[str(source)] = sha(source)
        for name in protocol['recovery_reports']:
            recovery = json.loads(Path(name).read_text())
            assert recovery['status'] == 'missing_receipt_only_frozen_mode_reaudit_passed_without_rerouting'
            for source, expected in recovery['source_sha256'].items():
                assert sha(source) == expected, source
            assert recovery['joint_quality_pass'] is True
            row, = [v for v in adjusted['cases'] if v['label'] == recovery['label']]
            assert row['status'] == 'upstream_failure_retained_no_capacity_fallback'
            assert row['mode_status'] == recovery['original_mode_status'] == 'native_mode_audit_error_retained_no_replay'
            changes.append({'label': row['label'], 'original_result': copy.deepcopy(row), 'recovery_audit': name})
            row.update(status='joint_pass_before_capacity_fallback', joint_quality_pass=True,
                       final_report=recovery['mode_report'], recovery_audit=name)
            refs[name] = sha(name)
        view_protocol['source_sha256'].update(refs)
        write(view / 'protocol.json', view_protocol)
        write(view / 'manifest.json', adjusted)
        for command, log in [
            ([sys.executable, protocol['aggregator'], protocol['baselines'], str(view), str(directory / 'reconciled_cohort_audit.json')], 'aggregate.log'),
            ([sys.executable, protocol['identity_auditor'], str(directory / 'reconciled_cohort_audit.json'), protocol['baselines'], str(directory / 'reconciled_native_identity_audit.json')], 'identity.log'),
        ]:
            with (directory / log).open('x') as stream:
                subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)
        for path in [directory / 'protocol.json', view / 'manifest.json', view / 'protocol.json',
                     directory / 'reconciled_cohort_audit.json', directory / 'reconciled_native_identity_audit.json', Path(__file__).resolve()]:
            refs[str(path)] = sha(path)
        write(directory / 'reconciliation_audit.json', {
            'status': 'original_failures_preserved_reviewed_receipt_recovery_aggregate_ready', 'changes': changes,
            'source_sha256': refs, 'research_complete': False,
            'scope': 'Additive recovered-quality aggregate only. Original mode/capacity/summary failure records unchanged. Recovered launch receipt is explicitly posthoc. No rerouting, policy tuning, resampling, full pipeline repeat, statistical generalization or board claim.'})
        state['status'] = 'reconciled_quality_and_native_identity_audits_ready'
        save()
    except BaseException:
        state.update(status='receipt_reconciliation_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
