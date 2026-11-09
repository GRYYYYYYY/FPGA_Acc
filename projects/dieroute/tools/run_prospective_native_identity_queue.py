"""Run the final native identity audit once the original summary finishes."""
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
    assert not (directory / 'manifest.json').exists(), 'No replay'
    state = {'status': 'waiting_for_original_summary', 'pid': os.getpid(), 'research_complete': False}

    def save():
        temp = directory / 'manifest.tmp'
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(directory / 'manifest.json')

    try:
        for name, expected in protocol['source_sha256'].items():
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
        save()
        while True:
            upstream = json.loads(Path(protocol['summary_manifest']).read_text())
            if upstream['status'] == 'terminal_summary_ready':
                break
            assert upstream['status'] not in ['summary_error_requires_review', 'summary_queue_stopped_requires_review']
            owner = protocol['summary_owner']
            text = (Path('/proc') / str(owner['pid']) / 'stat').read_text()
            fields = text[text.rfind(')') + 2:].split()
            assert fields[0] != 'Z' and fields[19] == owner['start_ticks'], 'Original summary owner gone'
            time.sleep(10)
        state['status'] = 'checking_final_native_identities'
        save()
        with (directory / 'audit.log').open('x') as stream:
            code = subprocess.call(protocol['command'], stdout=stream, stderr=subprocess.STDOUT)
        state.update(status='final_native_identity_audit_ready' if code == 0 else 'native_identity_audit_failed_requires_review', returncode=code)
        save()
    except BaseException:
        state.update(status='native_identity_queue_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
