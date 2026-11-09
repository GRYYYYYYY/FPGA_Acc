"""Wait for the existing retention-only run; never launch/retry a model."""
import datetime
import json
import os
import resource
import sys
import time
from pathlib import Path
import neuron_no_retention_trial_v2 as trial
from observe_neuron_scaled_present_pipeline_v1 import process

OUT = trial.R/'experiments/neuron_no_retention_postprocess_v1_2026-10-17'


def readiness(terminal, observed):
    gone = observed.get('status') == 'missing_not_terminal_evidence' or observed.get('verified_identity') is False or observed.get('state') in ('Z', 'X')
    if terminal is None:
        return 'unresolved' if gone else 'waiting'
    if type(terminal.get('exit_status')) is not int or terminal['exit_status'] != 0:
        return 'failed'
    if terminal.get('all_stages_completed') is not True:
        return 'unresolved'
    return 'ready' if gone else 'waiting'


def main():
    validation = trial.load(trial.R/'experiments/no_retention_postprocess_guard_v1_2026-10-17/verification.json')
    assert validation['all_pass']
    trial.check(validation['bindings'])
    metadata_path = trial.OUT/'process.json'
    metadata = trial.load(metadata_path)
    ticks = int(metadata['start_stat'].rsplit(')', 1)[1].split()[19])
    observed = process(metadata['pid'], ticks, metadata['args'])
    assert observed.get('verified_live') and observed.get('command_matches'), 'Existing run owner not verified live'
    assert not (trial.OUT/'metrics').exists() and not (trial.OUT/'independent_final_admission_v1.json').exists()
    hard = resource.getrlimit(resource.RLIMIT_AS)[1]
    assert hard == resource.RLIM_INFINITY or hard >= 8*2**30
    resource.setrlimit(resource.RLIMIT_AS, (192*2**20, hard))
    bindings = {str(p.resolve()):trial.sha(p) for p in (Path(__file__),Path(trial.__file__),metadata_path,trial.OUT/'protocol.json')}
    trial.check(trial.load(trial.OUT/'protocol.json')['bindings'])
    OUT.mkdir()
    trial.write(OUT/'process.json', dict(pid=os.getpid(),start_stat=Path('/proc/self/stat').read_text(),args=Path('/proc/self/cmdline').read_bytes().decode().rstrip('\0').split('\0')))
    trial.write(OUT/'protocol.json', dict(bindings=bindings,existing_model_only=True,stages=['admit','metrics'],no_model_launch_or_retry=True,stage_timeout_seconds=3600))
    try:
        while True:
            trial.check(bindings)
            observed = process(metadata['pid'], ticks, metadata['args'])
            terminal_path = trial.OUT/'pipeline_terminal.json'
            terminal = trial.load(terminal_path) if terminal_path.exists() else None
            state = readiness(terminal, observed)
            temp = OUT/'status.tmp'
            temp.write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),phase=state,predecessor=observed))+'\n')
            temp.replace(OUT/'status.json')
            if state == 'ready':
                break
            assert state == 'waiting', 'Predecessor failed or ambiguous; preserve evidence and stop'
            if observed.get('verified_identity') and observed.get('command_matches') is False:
                raise AssertionError('Existing run owner command changed')
            time.sleep(5)
        for name in ('model','initial_audit','sketch_audit','event_audit'):
            assert trial.load(trial.OUT/(name+'_terminal.json'))['exit_status'] == 0
            assert trial.gone(trial.OUT,name+'_process.json')
        for stage, limit in (('admit',512*2**20),('metrics',8*2**30)):
            trial.check(bindings)
            trial.run_stage(OUT,stage,[Path(trial.__file__),stage],limit,3600)
        proof = trial.load(trial.OUT/'metrics/verification.json')
        assert proof['all_pass'] and proof['independently_checked_metric_sets'] == 8
        assert trial.load(trial.OUT/'independent_final_admission_v1.json')['all_pass']
        trial.write(OUT/'terminal.json',dict(exit_status=0,closed_admission_and_all8_metrics_completed=True,promoted=False,goal_complete=False))
    except BaseException as error:
        trial.write(OUT/'terminal.json',dict(exit_status=1,error_type=type(error).__name__,error=str(error),no_retry=True))
        raise


if __name__ == '__main__':
    main()
