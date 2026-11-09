"""Explicit ownership handoff after diagnosed prelaunch-memory deferral.

Preserves the failed old queues and completed factor2 stages. No numerical retry.
"""
import argparse
import datetime
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from run_neuron_scaled_present_followup_v1 import predecessor_gate, owner_state
from run_neuron_scaled_present_pipeline_v1 import memory_admission, stage_action

OUT = R/'experiments/neuron_scaled_present_recovery_v1_2026-10-17'
PREFLIGHT = R/'experiments/neuron_scaled_present_recovery_preflight_v1_2026-10-17/verification.json'
DRIVER = R/'tools/run_neuron_scaled_present_pipeline_v1.py'
FINAL = R/'tools/verify_neuron_scaled_present_final_v1.py'


def read(path):
    return json.loads(path.read_text())


def check(bindings):
    for path, digest in bindings.items():
        assert sha(path) == digest, ('recovery input/source drift', path)


def case(factor):
    return R/f'experiments/titan23_neuron_scaled_present_factor{factor}_pipeline_v1_2026-10-15'


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def status(**value):
    temporary = OUT/'status.tmp'
    temporary.write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), **value), indent=2)+'\n')
    temporary.replace(OUT/'status.json')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    pre = read(PREFLIGHT)
    assert pre['all_pass'] is True and pre['event_audit_never_started'] is True
    assert pre['sole_failure_is_prelaunch_memory_admission'] is True
    assert all(stage_action(read(case(2)/(stage+'_terminal.json')), True) == 'done'
               for stage in ('model', 'initial_audit', 'sketch_audit'))
    assert not any((case(2)/('event_audit'+suffix)).exists()
                   for suffix in ('_terminal.json', '_process.json', '.log'))
    assert not case(4).exists()
    # Historical nonzero terminals plus current identities establish handoff.
    for root in (R/'experiments/neuron_scaled_present_followup_v1_2026-10-15',
                 R/'experiments/neuron_scaled_metric_followup_v2_2026-10-15'):
        assert read(root/'terminal.json')['exit_status'] == 1
        metadata = read(root/'process.json')
        ticks = int(metadata['start_stat'].rsplit(')', 1)[1].split()[19])
        assert owner_state(metadata['pid'], ticks) == 'gone'
    check(pre['bindings'])
    if not args.run:
        print('Ready for explicit factor2 unstarted audit continuation and full factor4.')
        return
    hard = resource.getrlimit(resource.RLIMIT_AS)[1]
    assert hard == resource.RLIM_INFINITY or hard >= 20*2**30
    resource.setrlimit(resource.RLIMIT_AS, (192*2**20, hard))
    sources = closure([Path(__file__), DRIVER, FINAL])
    sources[str(PREFLIGHT)] = sha(PREFLIGHT)
    check(sources)
    OUT.mkdir()
    write(OUT/'protocol.json', dict(bindings=sources, frozen_completed_factor2_bindings=pre['bindings'],
        model_submit_owner=True, stage_order=['continue_factor2', 'admit_factor2', 'factor4', 'admit_factor4'],
        policy='Only diagnosed never-started factor2 event audit/final metadata are resumed by unchanged original controller. All completed model/physical stages and failed old queues preserved. Factor4 starts once only after complete factor2. No recovery/retry of failed or ambiguous stages. Original20GiB model,8GiB audits and8GiB shared margin remain.',
        original_experiment_and_metric_policy_unchanged=True, goal_complete=False))
    write(OUT/'process.json', dict(pid=os.getpid(), args=sys.argv,
        start_stat=Path('/proc/self/stat').read_text()))
    stages = [('continue_factor2', 8*2**30, [sys.executable, str(DRIVER), '2', '--run']),
              ('admit_factor2', 512*2**20, [sys.executable, str(FINAL), '2']),
              ('factor4', 20*2**30, [sys.executable, str(DRIVER), '4', '--run']),
              ('admit_factor4', 512*2**20, [sys.executable, str(FINAL), '4'])]
    try:
        for name, limit, command in stages:
            check(sources)
            if name == 'factor4':
                assert predecessor_gate(case(2), 2, 'gone')['status'] == 'ready'
                assert read(case(2)/'independent_final_admission_v1.json')['all_pass'] is True
                assert not case(4).exists(), 'Refuse duplicate factor4 submission'
            while True:
                check(sources)
                admission = memory_admission(limit, int(Path('/sys/fs/cgroup/memory.current').read_text()),
                                             int(Path('/sys/fs/cgroup/memory.max').read_text()))
                if admission['admitted']:
                    break
                status(phase='waiting_for_memory', next_stage=name, admission=admission)
                time.sleep(30)
            write(OUT/(name+'_admission.json'), admission)
            with (OUT/(name+'.log')).open('x') as log:
                # Controller children retain inherited hard ceiling so their own
                # original per-stage preexec limits can be set without alteration.
                child = subprocess.Popen(command, cwd=R, stdout=log, stderr=subprocess.STDOUT)
                metadata = dict(pid=child.pid, args=command, start_stat=Path(f'/proc/{child.pid}/stat').read_text())
                write(OUT/(name+'_process.json'), metadata)
                status(phase='stage_running', stage=name, child_pid=child.pid)
                print('RECOVERY START', name, child.pid, flush=True)
                code = child.wait()
            write(OUT/(name+'_terminal.json'), dict(exit_status=code))
            if code:
                raise RuntimeError('Continuation stage failed; no retry: '+name)
        check(sources)
        check(pre['bindings'])
        assert predecessor_gate(case(4), 4, 'gone')['status'] == 'ready'
        status(phase='all_followup_factors_complete', goal_complete=False)
        write(OUT/'terminal.json', dict(exit_status=0, all_planned_followup_factors_completed=True,
                                      recovered_factor2_without_model_rerun=True, goal_complete=False))
    except BaseException as error:
        status(phase='stopped_requires_analysis', error=type(error).__name__+': '+str(error))
        write(OUT/'terminal.json', dict(exit_status=1, all_planned_followup_factors_completed=False, error=str(error)))
        raise


if __name__ == '__main__':
    main()
