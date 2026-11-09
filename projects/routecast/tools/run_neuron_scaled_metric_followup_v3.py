"""Single postprocessing owner; never submits, signals or recovers a model."""
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
from observe_neuron_scaled_present_pipeline_v1 import process
from evaluate_neuron_scaled_present_full_comparison_v2 import owner_gone

QUEUE = R/'experiments/neuron_scaled_present_recovery_v1_2026-10-17'
OUT = R/'experiments/neuron_scaled_metric_followup_v3_2026-10-17'
COMPARISON = R/'experiments/neuron_scaled_present_full_comparison_v2_2026-10-17'


def load(path):
    with path.open('rb') as stream:
        raw = stream.read(2**20+1)
    assert len(raw) <= 2**20, 'metadata over1MiB'
    value = json.loads(raw)
    assert type(value) is dict
    return value


def predecessor(terminal, gone):
    if terminal is None:
        return 'unresolved' if gone else 'waiting'
    if type(terminal.get('exit_status')) is not int or terminal['exit_status'] != 0:
        return 'failed'
    if terminal.get('all_planned_followup_factors_completed') is not True:
        return 'unresolved'
    return 'ready' if gone else 'waiting'


def check(bindings):
    for path, digest in bindings.items():
        assert sha(path) == digest, ('postprocessing source drift', path)


def status(**value):
    value = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), **value)
    temporary = OUT/'status.tmp'
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(OUT/'status.json')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    metadata = load(QUEUE/'process.json')
    ticks = int(metadata['start_stat'].rsplit(')', 1)[1].split()[19])
    identity = process(metadata['pid'], ticks)
    if not args.run:
        print(json.dumps(dict(predecessor_owner=identity, evaluation_prepared=(COMPARISON/'protocol.json').exists())))
        return
    assert not (R/'experiments/neuron_scaled_metric_followup_v1_2026-10-15').exists(), 'Earlier postprocessing owner exists; refuse duplicate'
    failed_prior=R/'experiments/neuron_scaled_metric_followup_v2_2026-10-15'
    assert load(failed_prior/'terminal.json')['exit_status']==1
    prior=load(failed_prior/'process.json')
    prior_ticks=int(prior['start_stat'].rsplit(')',1)[1].split()[19])
    assert owner_gone(process(prior['pid'],prior_ticks)), 'Prior postprocessing owner not confirmed gone'
    own_limit = 192*2**20
    own_margin = 64*2**20
    free = int(Path('/sys/fs/cgroup/memory.max').read_text()) - int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free >= own_limit + own_margin, 'Light controller launch deferred by shared memory gate'
    inherited_hard = resource.getrlimit(resource.RLIMIT_AS)[1]
    assert inherited_hard == resource.RLIM_INFINITY or inherited_hard >= 8*2**30
    resource.setrlimit(resource.RLIMIT_AS, (own_limit, inherited_hard))
    # Bind only source and small immutable metadata during routine waiting.
    bindings = closure([Path(__file__)])
    for path in (QUEUE/'process.json', COMPARISON/'protocol.json'):
        bindings[str(path)] = sha(path)
    comparison = load(COMPARISON/'protocol.json')
    for path, digest in comparison['bindings'].items():
        assert path not in bindings or bindings[path] == digest
        bindings[path] = digest
    check(bindings)
    OUT.mkdir()
    (OUT/'protocol.json').write_text(json.dumps(dict(bindings=bindings,
        predecessor_queue=str(QUEUE), controller_soft_limit_bytes=own_limit, controller_margin_bytes=own_margin,
        child_stage_margin_bytes=8*2**30, controller_shared_headroom_before_bytes=free, stage_order=['admit_factor2', 'admit_factor4', 'full_metric_comparison'],
        policy='Only after complete successful predecessor queue and original owner exit. Each child has fresh actual cap+8GiB margin. No model submission, signalling, retry, recovery, factor selection or promotion. Unknown predecessor evidence/source drift/nonzero child stops for analysis.',
        goal_complete=False), indent=2)+'\n')
    (OUT/'process.json').write_text(json.dumps(dict(pid=os.getpid(), args=sys.argv,
        start_stat=Path('/proc/self/stat').read_text(), address_space_soft_limit_bytes=own_limit,
        address_space_hard_limit_bytes=inherited_hard))+'\n')
    try:
        while True:
            check(bindings)
            state = process(metadata['pid'], ticks)
            if state.get('status') == 'invalid_process_metadata':
                raise RuntimeError('Predecessor owner state unknown')
            terminal = load(QUEUE/'terminal.json') if (QUEUE/'terminal.json').exists() else None
            gate = predecessor(terminal, owner_gone(state))
            if gate in ('failed', 'unresolved'):
                raise RuntimeError('Predecessor refused: '+gate)
            if gate == 'ready':
                break
            status(phase='waiting_for_model_queue', predecessor_owner=state, predecessor_gate=gate)
            time.sleep(30)
        stages = []
        for factor in (2, 4):
            target = R/f'experiments/titan23_neuron_scaled_present_factor{factor}_pipeline_v1_2026-10-15/independent_final_admission_v1.json'
            if target.exists():
                proof = load(target)
                assert proof['all_pass'] is True and proof['present_factor'] == factor
                assert proof['all_original_connections'] == 77106 and proof['all_events'] == 101534
                check(proof['bindings'])
                status(phase='existing_complete_admission_verified', factor=factor)
                continue
            stages.append((f'admit_factor{factor}', 512*2**20,
                           [sys.executable, str(R/'tools/verify_neuron_scaled_present_final_v1.py'), str(factor)]))
        assert not (COMPARISON/'evaluation_started.json').exists(), 'Ambiguous existing comparison attempt'
        stages.append(('full_metric_comparison', 8*2**30,
                       [sys.executable, str(R/'tools/evaluate_neuron_scaled_present_full_comparison_v2.py'), 'run']))
        for name, limit, command in stages:
            while True:
                check(bindings)
                free = int(Path('/sys/fs/cgroup/memory.max').read_text()) - int(Path('/sys/fs/cgroup/memory.current').read_text())
                if free >= limit+8*2**30:
                    break
                status(phase='waiting_for_postprocessing_memory', next_stage=name,
                       shared_headroom_bytes=free, required_bytes=limit+8*2**30)
                time.sleep(30)
            # Keep a small parent soft cap and the inherited hard ceiling so the
            # child can set its own soft/hard stage limit before exec.
            with (OUT/(name+'.log')).open('x') as log:
                child = subprocess.Popen(command, cwd=R, stdout=log, stderr=subprocess.STDOUT,
                    preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_AS, (limit, limit)))
                (OUT/(name+'_process.json')).write_text(json.dumps(dict(pid=child.pid,
                    args=command, start_stat=Path(f'/proc/{child.pid}/stat').read_text(),
                    address_space_limit_bytes=limit))+'\n')
                status(phase='postprocessing_stage_running', stage=name, child_pid=child.pid)
                result = child.wait()
            (OUT/(name+'_terminal.json')).write_text(json.dumps(dict(exit_status=result))+'\n')
            if result != 0:
                raise RuntimeError('Postprocessing child failed: '+name)
        final = load(COMPARISON/'verification.json')
        assert final['all_pass'] is True and final['factors'] == [1, 2, 4]
        assert final['independently_checked_metric_sets'] == 12 and final['promoted'] is False
        check(bindings)
        status(phase='complete_requires_research_interpretation', goal_complete=False)
        (OUT/'terminal.json').write_text(json.dumps(dict(exit_status=0, comparison_completed=True, goal_complete=False))+'\n')
    except BaseException as error:
        status(phase='stopped_requires_analysis', error=type(error).__name__+': '+str(error))
        (OUT/'terminal.json').write_text(json.dumps(dict(exit_status=1, comparison_completed=False, error=str(error)))+'\n')
        raise


if __name__ == '__main__':
    main()
