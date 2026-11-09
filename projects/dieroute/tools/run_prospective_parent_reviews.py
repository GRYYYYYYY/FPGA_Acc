"""Review each prospective parent only after its original producer terminates."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback


def main():
    directory = Path(sys.argv[1]).resolve()
    protocol = json.loads((directory / 'protocol.json').read_text())
    assert not (directory / 'manifest.json').exists(), 'No implicit replay'
    state = {'status': 'waiting_for_original_parents', 'pid': os.getpid(), 'cases': [],
             'research_complete': False, 'board_result': False}

    def save():
        temp = directory / 'manifest.tmp'
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(directory / 'manifest.json')

    def verify():
        for name, expected in protocol['source_sha256'].items():
            digest = hashlib.sha256(Path(name).read_bytes()).hexdigest()
            assert digest == expected, name

    def owner_live():
        owner = protocol['original_owner']
        path = Path('/proc') / str(owner['pid']) / 'stat'
        if not path.exists():
            return False
        text = path.read_text()
        fields = text[text.rfind(')') + 2:].split()
        return fields[0] != 'Z' and fields[19] == owner['start_ticks']

    def producer():
        try:
            return json.loads(Path(protocol['parent_manifest']).read_text())
        except (OSError, json.JSONDecodeError):
            return {}

    try:
        verify()
        save()
        for case in protocol['cases']:
            label = case['label']
            state.update(status='waiting_for_original_parent_case', active_case=label)
            save()
            while True:
                parent_state = producer()
                step = next((v for v in parent_state.get('steps', []) if v['label'] == label), None)
                if step and step['status'] in ['passed', 'failed']:
                    break
                assert parent_state.get('status') != 'failed', parent_state.get('error')
                assert owner_live(), 'Original parent owner missing; reconcile without restart'
                time.sleep(10)
            folder = directory / label
            folder.mkdir()
            row = {'label': label, 'steps': [], 'parent_returncode': step['returncode']}
            state['cases'].append(row)
            if step['returncode'] != 0:
                row.update(status='parent_failed_no_review_or_resampling', native_legal=False)
                save()
                continue
            parent = Path(case['parent'])
            run = json.loads((parent / 'manifest.json').read_text())
            assert run['status'] == 'online_router_completed_equivalence_audit_required' and run['returncode'] == 0
            verify()
            state['status'] = 'reviewing_completed_parent'
            save()
            for recipe in case['steps']:
                if recipe['kind'] == 'writeback':
                    assert not (parent / 'native.route').exists(), 'Do not overwrite archived native route'
                start = time.monotonic_ns()
                record = {'label': recipe['label'], 'command': recipe['command'], 'status': 'running'}
                row['steps'].append(record)
                save()
                with (folder / (recipe['label'] + '.log')).open('x') as log:
                    child = subprocess.Popen(recipe['command'], cwd=protocol['cwd'], stdout=log, stderr=subprocess.STDOUT)
                    record['pid'] = child.pid
                    save()
                    code = child.wait()
                record.update(status='passed' if code == 0 else 'failed', returncode=code,
                              wall_ns=time.monotonic_ns() - start)
                save()
                if code:
                    row.update(status='parent_review_failed_outcome_retained', native_legal=False)
                    break
            else:
                quality = json.loads((parent / 'native_validation/validation.json').read_text())
                row.update(status='parent_tree_provenance_writeback_native_validation_terminal',
                           native_legal=quality['legal'], wirelength=quality['total_wirelength'],
                           cpd_ns=quality['critical_path_delay_ns'],
                           wl_cpd_nonincrease=(quality['total_wirelength'] <= quality['baseline_wirelength']
                                              and quality['critical_path_delay_ns'] <= quality['baseline_cpd_ns']))
            save()
        verify()
        state['status'] = 'five_prospective_parent_reviews_terminal_requires_analysis'
        save()
    except BaseException:
        state.update(status='parent_review_queue_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
