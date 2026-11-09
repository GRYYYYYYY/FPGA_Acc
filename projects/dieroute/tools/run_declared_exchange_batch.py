"""Execute each declared private search once; no replay or adoption."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback


def main():
    directory = Path(sys.argv[1]).resolve()
    protocol = json.loads((directory / 'batch_protocol.json').read_text())
    assert not (directory / 'batch_manifest.json').exists()
    state = {'status': 'running_declared_private_searches', 'pid': os.getpid(), 'cases': [], 'research_complete': False}

    def save():
        temp = directory / 'batch_manifest.tmp'
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(directory / 'batch_manifest.json')

    try:
        for name, expected in protocol['source_sha256'].items():
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
        save()
        for case in protocol['cases']:
            row = {'label': case['label'], 'status': 'search_running'}
            state['cases'].append(row)
            with (directory / (case['label'] + '.log')).open('x') as stream:
                child = subprocess.Popen(case['command'], stdout=stream, stderr=subprocess.STDOUT)
                row['pid'] = child.pid
                save()
                code = child.wait()
            row.update(status='private_search_terminal_requires_native_review' if code == 0 else 'private_search_error_retained', returncode=code)
            save()
        state['status'] = 'declared_private_searches_terminal_require_native_review'
        save()
    except BaseException:
        state.update(status='batch_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
