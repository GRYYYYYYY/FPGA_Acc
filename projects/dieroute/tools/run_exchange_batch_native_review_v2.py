"""Review a declared search batch once; retain search and native failures."""
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
    protocol = json.loads((directory / 'review_protocol.json').read_text())
    assert not (directory / 'review_manifest.json').exists()
    state = {'status': 'waiting_for_original_search_batch', 'pid': os.getpid(), 'cases': [], 'research_complete': False}

    def save():
        temp = directory / 'review_manifest.tmp'
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(directory / 'review_manifest.json')

    def live(owner):
        path = Path('/proc') / str(owner['pid']) / 'stat'
        if not path.exists():
            return False
        text = path.read_text()
        fields = text[text.rfind(')') + 2:].split()
        return fields[0] != 'Z' and fields[19] == owner['start_ticks']

    def run(command, log):
        with log.open('x') as stream:
            return subprocess.call(command, stdout=stream, stderr=subprocess.STDOUT)

    try:
        for name, expected in protocol['source_sha256'].items():
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
        save()
        while True:
            batch = json.loads(Path(protocol['batch_manifest']).read_text())
            if batch['status'] == 'declared_private_searches_terminal_require_native_review':
                break
            assert batch['status'] != 'batch_stopped_requires_review'
            assert live(protocol['batch_owner']), 'Original search owner gone; reconcile without replay'
            time.sleep(10)
        for case in protocol['cases']:
            generation = Path(case['generation'])
            generated = json.loads((generation / 'manifest.json').read_text())
            row = {'label': generation.name, 'search_arms': [
                {'name': a['name'], 'status': a['status']} for a in generated['arms']], 'native_audits': []}
            state['cases'].append(row)
            if not any(a.get('candidate_tree') for a in generated['arms']):
                row['status'] = 'no_complete_candidate_retained'
                save()
                continue
            state['status'] = 'preparing_native_checks'
            save()
            assert not (generation / 'native_queue').exists(), 'No implicit replay'
            code = run([sys.executable, protocol['preparer'], str(generation), case['template']], generation / 'prepare_native.log')
            if code:
                row.update(status='native_preparation_error_retained', returncode=code)
                save()
                continue
            queue = generation / 'native_queue'
            receipt = json.loads((queue / 'launch_receipt.json').read_text())
            # Read terminal state first, as short-lived owners can already exit.
            owner = None
            while True:
                try:
                    native = json.loads((queue / 'manifest.json').read_text())
                except (OSError, json.JSONDecodeError):
                    # Startup publication can lag behind launch. Observe the
                    # same child; never restart on a missing/partial manifest.
                    if owner is None:
                        text = (Path('/proc') / str(receipt['pid']) / 'stat').read_text()
                        fields = text[text.rfind(')') + 2:].split()
                        owner = {'pid': receipt['pid'], 'start_ticks': fields[19]}
                    assert live(owner), 'Native owner absent before manifest publication; reconcile without replay'
                    time.sleep(1)
                    continue
                if native['status'] == 'all_native_candidates_terminal_require_independent_review':
                    break
                assert native['status'] == 'serial_native_candidates_running', native
                if owner is None:
                    text = (Path('/proc') / str(receipt['pid']) / 'stat').read_text()
                    fields = text[text.rfind(')') + 2:].split()
                    owner = {'pid': receipt['pid'], 'start_ticks': fields[19]}
                assert live(owner), 'Native queue owner gone before terminal receipt; reconcile without replay'
                time.sleep(5)
            native_protocol = json.loads((queue / 'protocol.json').read_text())
            for candidate in native_protocol['cases']:
                arm = candidate['net']
                code = run([sys.executable, protocol['auditor'], str(generation), arm], generation / ('audit_' + arm + '.log'))
                item = {'arm': arm, 'audit_returncode': code}
                if code == 0:
                    path = queue / arm / 'independent_native_audit.json'
                    audit = json.loads(path.read_text())
                    item.update(report=str(path), checks=audit['checks'], wirelength=audit['wirelength'],
                                cpd_ns=audit['cpd_ns'], model_crossings=audit['model_crossings'])
                row['native_audits'].append(item)
            row['status'] = 'native_candidates_terminal_reviewed' if all(v['audit_returncode'] == 0 for v in row['native_audits']) else 'native_audit_error_retained'
            save()
        state['status'] = 'declared_batch_native_reviews_terminal_requires_interpretation'
        save()
    except BaseException:
        state.update(status='native_review_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
