"""Preserve stable routed checkpoints before producer cleanup, without modifying the build."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build = args.build.resolve()
    output = args.output.resolve()
    output.mkdir(exist_ok=False)
    producer = build / 'manifest.json'
    initial = json.loads(producer.read_text())
    proc = Path('/proc', str(initial['pid']), 'stat')
    identity = proc.read_text().split(')')[-1].split()[19]
    state = dict(status='watching_live_producer', pid=os.getpid(), producer_pid=initial['pid'],
                 producer_start_ticks=identity, checkpoints=[], board_result=False,
                 research_complete=False, script_sha256=sha(Path(__file__)),
                 scope='Stable byte copies only; checkpoint readability, finality, timing and signoff require separate validation.')

    def save():
        (output / 'manifest.json').write_text(json.dumps(state, indent=2) + '\n')

    observed = {}
    archived = set()
    save()
    while True:
        current = json.loads(producer.read_text())
        live = proc.exists() and proc.read_text().split(')')[-1].split()[19] == identity
        for path in build.rglob('*_routed.dcp'):
            if path.parent.name != 'impl_1' or '/.local/' in str(path):
                continue
            try:
                stat = path.stat()
                signature = (stat.st_size, stat.st_mtime_ns)
                if not stat.st_size or observed.get(path) != signature:
                    observed[path] = signature
                    continue
                before = sha(path)
                if before in archived:
                    continue
                temporary = output / 'copy.partial'
                shutil.copyfile(path, temporary)
                if sha(temporary) != before or sha(path) != before:
                    temporary.unlink(missing_ok=True)
                    continue
                target = output / (before + '.dcp')
                temporary.replace(target)
                archived.add(before)
                state['checkpoints'].append(dict(source=str(path), copy=str(target),
                                                sha256=before, bytes=stat.st_size,
                                                producer_status=current['status'], captured_ns=time.time_ns()))
                save()
            except FileNotFoundError:
                continue
        if not live:
            state.update(status='producer_exited_copies_require_validation' if archived else
                         'producer_exited_no_routed_checkpoint_captured',
                         producer_terminal_status=current['status'])
            save()
            break
        time.sleep(5)


if __name__ == '__main__':
    main()
