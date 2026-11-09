"""Add missing execution receipts; distinguish live observation from reconstruction."""
import hashlib
import json
from pathlib import Path
import sys
import time
import os
import traceback


def main():
    directory = Path(sys.argv[1]).resolve()
    protocol = json.loads((directory / 'protocol.json').read_text())
    assert not (directory / 'manifest.json').exists()
    state = {'status': 'watching_original_mode_owner', 'pid': os.getpid(), 'receipts': [], 'research_complete': False}

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
        while True:
            for label in protocol['labels']:
                for mode in ['wirelength', 'delay']:
                    folder = Path(protocol['mode_root']) / label / mode
                    receipt_path = folder / 'launch_receipt.json'
                    manifest_path = folder / 'manifest.json'
                    if receipt_path.exists() or not manifest_path.exists():
                        continue
                    manifest = json.loads(manifest_path.read_text())
                    terminal = manifest['status'].startswith('experiment_terminal_')
                    receipt = {'status': 'reconstructed_after_terminal_missing_original_launch_receipt' if terminal else 'live_actor_observation_missing_original_launch_receipt',
                               'actor_pid_from_manifest': manifest['pid'], 'observed_ns': time.time_ns(),
                               'original_launch_time_ns': None,
                               'scope': 'Supplemental execution receipt, not a claim of contemporaneous launch capture or an independent rerun.',
                               'source_sha256': {str(folder / 'protocol.json'): sha(folder / 'protocol.json'),
                                                 str(Path(__file__).resolve()): sha(Path(__file__).resolve())}}
                    if terminal:
                        receipt['terminal_manifest_sha256'] = sha(manifest_path)
                    else:
                        proc = Path('/proc') / str(manifest['pid'])
                        text = (proc / 'stat').read_text()
                        fields = text[text.rfind(')') + 2:].split()
                        assert fields[0] != 'Z'
                        argv = (proc / 'cmdline').read_bytes().split(b'\0')
                        assert str(folder).encode() in argv and str(protocol['actor']).encode() in argv
                        receipt.update(process_start_ticks=fields[19], observed_argv=[v.decode() for v in argv if v])
                    with receipt_path.open('x') as stream:
                        json.dump(receipt, stream, indent=2)
                        stream.write('\n')
                    state['receipts'].append({'label': label, 'mode': mode, 'path': str(receipt_path), 'status': receipt['status']})
                    save()
            root_state = json.loads((Path(protocol['mode_root']) / 'manifest.json').read_text())
            if root_state['status'] in ['five_prospective_native_mode_cases_terminal_requires_interpretation', 'native_mode_queue_stopped_requires_review']:
                state['status'] = 'original_mode_owner_terminal_receipt_watch_complete'
                save()
                return
            owner = protocol['owner']
            text = (Path('/proc') / str(owner['pid']) / 'stat').read_text()
            fields = text[text.rfind(')') + 2:].split()
            assert fields[0] != 'Z' and fields[19] == owner['start_ticks']
            time.sleep(5)
    except BaseException:
        state.update(status='receipt_watch_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
