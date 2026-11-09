"""Run one frozen HLS synthesis with durable state and an actual exit receipt."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    args = parser.parse_args()
    package = args.package.resolve()
    lock = (package / 'synthesis.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not (package / 'synthesis_state.json').exists(), 'Already submitted'
    manifest = json.loads((package / 'manifest.json').read_text())
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    def mismatches():
        return [n for n, h in manifest['files'].items() if sha(package / n) != h]
    assert not mismatches()
    state = {'supervisor_pid': os.getpid(), 'manifest_sha256': sha(package / 'manifest.json')}
    def save(name):
        state['observed_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        tmp = package / (name + '.tmp')
        tmp.write_text(json.dumps(state, indent=2) + '\n')
        tmp.replace(package / name)
    command = ['bash', '-c', 'source "$1"\nexec vitis_hls -f "$2"', 'frozen-synthesis',
               '/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis/2022.2/settings64.sh',
               str(package / 'run_synth.tcl')]
    with (package / 'synthesis.log').open('x') as log:
        job = subprocess.Popen(command, cwd=package, stdout=log, stderr=subprocess.STDOUT,
                               start_new_session=True)
        state.update(command=command, job_pid=job.pid, status='running')
        while True:
            save('synthesis_state.json')
            try:
                rc = job.wait(timeout=60)
                break
            except subprocess.TimeoutExpired:
                continue
    state.update(returncode=rc, status='terminal', source_mismatches=mismatches(),
                 log_sha256=sha(package / 'synthesis.log'))
    state['synthesis_gate_pass'] = rc == 0 and not state['source_mismatches']
    save('synthesis_terminal.json')
    return 0 if state['synthesis_gate_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
