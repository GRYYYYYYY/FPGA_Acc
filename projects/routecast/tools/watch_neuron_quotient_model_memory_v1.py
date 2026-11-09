"""Read-only PID/start/argv-bound memory sampling; no submission or signals."""
import datetime
import hashlib
import json
import os
import resource
import time
from pathlib import Path

from observe_neuron_scaled_present_pipeline_v1 import process

R = Path(__file__).resolve().parents[1]
CASE = R/'experiments/neuron_quotient_astar_pipeline_v1_2026-10-17'
OUT = R/'experiments/neuron_quotient_memory_watch_v1_2026-10-17'


def main():
    resource.setrlimit(resource.RLIMIT_AS, (64*2**20, 64*2**20))
    metadata_path = CASE/'model_process.json'
    raw = metadata_path.read_bytes()
    metadata = json.loads(raw)
    ticks = int(metadata['start_stat'].rsplit(')', 1)[1].split()[19])
    initial = process(metadata['pid'], ticks, metadata['args'])
    assert initial['verified_live']
    OUT.mkdir()
    (OUT/'protocol.json').write_text(json.dumps(dict(
        metadata_path=str(metadata_path), metadata_sha256=hashlib.sha256(raw).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        interval_seconds=1, initial_process=initial, reads_only_procfs=True,
        scope='VmHWM includes process history before observer start. Sampled HWM/RSS maxima are lower bounds on full process peaks: a final subsecond allocation may be missed. No process signaling, model changes, stage submission or recovery.'), indent=2)+'\n')
    (OUT/'process.json').write_text(json.dumps(dict(pid=os.getpid(),
        start_stat=Path('/proc/self/stat').read_text(),
        args=Path('/proc/self/cmdline').read_bytes().decode().rstrip('\0').split('\0')))+'\n')
    maxima = dict(VmRSS=0, VmHWM=0, VmSize=0)
    samples = 0
    with (OUT/'samples.jsonl').open('x') as stream:
        while True:
            observed = process(metadata['pid'], ticks, metadata['args'])
            row = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), **observed)
            stream.write(json.dumps(row)+'\n')
            stream.flush()
            samples += 1
            for key, value in observed.get('memory_KiB', {}).items():
                maxima[key] = max(maxima[key], value)
            if observed.get('status') == 'missing_not_terminal_evidence' or observed.get('verified_identity') is False or observed.get('state') in ('Z', 'X'):
                break
            if observed.get('verified_identity') is True and observed.get('command_matches') is False:
                raise RuntimeError('PID changed executable/argv; observer stops for analysis')
            time.sleep(1)
    terminal = CASE/'model_terminal.json'
    value = dict(exit_status=0, observer_completed=True, samples=samples,
        sampled_maxima_KiB=maxima, final_process_observation=observed,
        model_terminal=json.loads(terminal.read_text()) if terminal.exists() else None,
        exact_full_process_peak_proven=False, model_success_inferred_from_absence=False)
    (OUT/'terminal.json').write_text(json.dumps(value, indent=2)+'\n')
    print(json.dumps(value), flush=True)


if __name__ == '__main__':
    main()
