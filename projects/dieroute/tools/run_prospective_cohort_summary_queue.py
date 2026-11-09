"""Wait for the original capacity owner, then aggregate once; no replay."""
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
    state = {'status': 'waiting_for_original_capacity_owner', 'pid': os.getpid(), 'research_complete': False}

    def save():
        temp = directory / 'manifest.tmp'
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(directory / 'manifest.json')

    try:
        for name, expected in protocol['source_sha256'].items():
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
        save()
        while True:
            manifest = json.loads(Path(protocol['capacity_manifest']).read_text())
            if manifest['status'] == 'five_prospective_policy_cases_terminal_require_final_cohort_audit':
                break
            assert manifest['status'] != 'capacity_fallback_queue_stopped_requires_review'
            owner = protocol['capacity_owner']
            text = (Path('/proc') / str(owner['pid']) / 'stat').read_text()
            fields = text[text.rfind(')') + 2:].split()
            assert fields[0] != 'Z' and fields[19] == owner['start_ticks'], 'Original owner gone; reconcile without restarting'
            time.sleep(10)
        state['status'] = 'aggregating_terminal_reports'
        save()
        with (directory / 'audit.log').open('x') as stream:
            code = subprocess.call(protocol['command'], stdout=stream, stderr=subprocess.STDOUT)
        state.update(status='terminal_summary_ready' if code == 0 else 'summary_error_requires_review', returncode=code)
        save()
    except BaseException:
        state.update(status='summary_queue_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
