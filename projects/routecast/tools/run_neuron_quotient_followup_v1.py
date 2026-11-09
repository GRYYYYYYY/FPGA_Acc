"""Single future-candidate owner; waits for old model+metrics to close.

Explicit authorized chain only. Failed or ambiguous stages are never retried.
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

from run_neuron_quotient_astar_pipeline_v1 import R, OUT as CANDIDATE, METRIC_QUEUE, DIAGNOSTIC, gone
from observe_neuron_scaled_present_pipeline_v1 import process
from evaluate_neuron_quotient_astar_full_comparison_v1 import OUT as METRICS

sys.path.insert(0, str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha

OUT = R/'experiments/neuron_quotient_followup_v1_2026-10-17'
DRIVER = R/'tools/run_neuron_quotient_astar_pipeline_v1.py'
FINAL = R/'tools/verify_neuron_quotient_final_admission_v1.py'
EVALUATOR = R/'tools/evaluate_neuron_quotient_astar_full_comparison_v1.py'


def load(path):
    with Path(path).open('rb') as stream:
        data = stream.read(2**20+1)
    assert len(data) <= 2**20, 'metadata over1MiB'
    return json.loads(data)


def predecessor(terminal, owner_gone):
    if terminal is None:
        return 'unresolved' if owner_gone else 'waiting'
    if type(terminal.get('exit_status')) is not int or terminal['exit_status'] != 0:
        return 'failed'
    if terminal.get('comparison_completed') is not True:
        return 'unresolved'
    return 'ready' if owner_gone else 'waiting'


def stage_action(terminal, started):
    if terminal is not None:
        return 'done' if type(terminal.get('exit_status')) is int and terminal['exit_status'] == 0 else 'failed'
    return 'unresolved_started_stage' if started else 'launch'


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def status(**value):
    temp = OUT/'status.tmp'
    temp.write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), **value), indent=2)+'\n')
    temp.replace(OUT/'status.json')


def check(bindings):
    assert all(sha(path) == digest for path, digest in bindings.items()), 'Frozen queue binding drift'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    assert load(DIAGNOSTIC/'closed_construction_admission_v1.json')['all_pass'] is True
    assert load(DIAGNOSTIC/'terminal.json')['exit_status'] == 0 and gone(DIAGNOSTIC)
    assert not (CANDIDATE/'process.json').exists(), 'Candidate already submitted/ambiguous'
    assert not (METRICS/'evaluation_started.json').exists()
    assert load(CANDIDATE/'protocol.json')['present_factor'] == 1
    assert load(CANDIDATE/'protocol.json')['cache_entries'] == 512
    metadata = load(METRIC_QUEUE/'process.json')
    ticks = int(metadata['start_stat'].rsplit(')', 1)[1].split()[19])
    state = process(metadata['pid'], ticks)
    if not args.run:
        print(json.dumps(dict(predecessor=state, candidate_prepared=True, model_submitted=False)))
        return
    hard = resource.getrlimit(resource.RLIMIT_AS)[1]
    assert hard == resource.RLIM_INFINITY or hard >= 20*2**30
    own_limit = 192*2**20
    free = int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free >= own_limit+64*2**20
    resource.setrlimit(resource.RLIMIT_AS, (own_limit, hard))
    bindings = closure([Path(__file__), FINAL, DRIVER, EVALUATOR])
    for path in (METRIC_QUEUE/'process.json', CANDIDATE/'protocol.json', METRICS/'protocol.json',
        DIAGNOSTIC/'closed_construction_admission_v1.json',
        R/'experiments/neuron_quotient_launch_gate_contract_v1_2026-10-17/verification.json',
        R/'experiments/neuron_quotient_metric_policy_contract_v1_2026-10-17/verification.json'):
        bindings[str(path)] = sha(path)
    check(bindings)
    OUT.mkdir()
    write(OUT/'process.json', dict(pid=os.getpid(), start_stat=Path('/proc/self/stat').read_text(),
        args=Path('/proc/self/cmdline').read_bytes().decode().rstrip('\0').split('\0')))
    write(OUT/'protocol.json', dict(bindings=bindings, predecessor_queue=str(METRIC_QUEUE),
        controller_soft_limit_bytes=own_limit, inherited_hard_limit=hard,
        stage_order=['candidate_full_pipeline', 'closed_final_admission', 'all8_metric_comparison'],
        candidate_factor=1, candidate_cache_entries=512,
        admission_margin_bytes=8*2**30,
        policy='Wait successful original factor1/2/4 model+audit+12metric chain and owner gone; run frozen fixedfactor1/cache512 candidate once, complete all audits, separate closed admission, all8 metrics. No retry/recovery/factor selection/default promotion.',
        original_jobs_untouched=True, goal_complete=False))
    stages = [('candidate_full_pipeline', 20*2**30, [sys.executable, str(DRIVER), 'run']),
        ('closed_final_admission', 512*2**20, [sys.executable, str(FINAL)]),
        ('all8_metric_comparison', 8*2**30, [sys.executable, str(EVALUATOR), 'run'])]
    try:
        while True:
            check(bindings)
            state = process(metadata['pid'], ticks)
            try:
                terminal = load(METRIC_QUEUE/'terminal.json')
            except FileNotFoundError:
                terminal = None
            except json.JSONDecodeError:
                status(phase='waiting_for_valid_predecessor_observation', predecessor_owner=state)
                time.sleep(30)
                continue
            gate = predecessor(terminal, gone(METRIC_QUEUE))
            if gate in ('failed', 'unresolved'):
                raise RuntimeError('Original postprocessing '+gate+'; no candidate submitted')
            if gate == 'ready':
                break
            status(phase='waiting_for_original_full_metrics', predecessor_owner=state, gate=gate)
            time.sleep(30)
        for name, limit, command in stages:
            check(bindings)
            assert stage_action(None, any((OUT/(name+suffix)).exists() for suffix in ('_process.json', '.log', '_terminal.json'))) == 'launch'
            while True:
                free = int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
                if free >= limit+8*2**30:
                    break
                status(phase='waiting_for_stage_memory', next_stage=name, shared_headroom_bytes=free)
                time.sleep(30)
                check(bindings)
            write(OUT/(name+'_admission.json'), dict(shared_headroom_bytes=free,
                child_limit_bytes=limit, margin_bytes=8*2**30))
            with (OUT/(name+'.log')).open('x') as log:
                # Pipeline controller needs the inherited hard ceiling for its
                # explicit20/8GiB children. Final/evaluator children are capped.
                cap = (own_limit, hard) if name == 'candidate_full_pipeline' else (limit, limit)
                child = subprocess.Popen(command, cwd=R, stdout=log, stderr=subprocess.STDOUT,
                    preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_AS, cap))
                write(OUT/(name+'_process.json'), dict(pid=child.pid, args=command,
                    start_stat=Path('/proc', str(child.pid), 'stat').read_text()))
                status(phase='stage_running', stage=name, child_pid=child.pid)
                print('QUOTIENT FOLLOWUP START', name, child.pid, flush=True)
                code = child.wait()
            write(OUT/(name+'_terminal.json'), dict(exit_status=code))
            if code:
                raise RuntimeError('Candidate chain failed: '+name+'; no retry')
        assert load(CANDIDATE/'independent_final_admission_v1.json')['all_pass'] is True
        comparison = load(METRICS/'verification.json')
        assert comparison['all_pass'] is True and comparison['independently_checked_metric_sets'] == 8
        assert comparison['promoted'] is False
        check(bindings)
        write(OUT/'terminal.json', dict(exit_status=0, full_candidate_and_all8_metrics_completed=True,
            requires_research_interpretation=True, goal_complete=False))
        status(phase='complete_requires_research_interpretation', goal_complete=False)
    except BaseException as error:
        write(OUT/'terminal.json', dict(exit_status=1, error=type(error).__name__+': '+str(error),
            full_candidate_and_all8_metrics_completed=False, goal_complete=False))
        status(phase='stopped_requires_analysis', error=str(error))
        raise


if __name__ == '__main__':
    main()
