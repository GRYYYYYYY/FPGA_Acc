"""Single complete continuation trial: run, separate admit, all8 metrics; no retry."""
import os
import resource
import subprocess
import sys
from pathlib import Path
import neuron_proxy_budget_trial_v1 as trial
from source_binding_v2 import closure

OUT=trial.R/'experiments/neuron_proxy_budget_full_chain_v1_2026-10-17'


def main():
    guard=trial.R/'experiments/neuron_proxy_budget_trial_guard_v1_2026-10-17/verification.json'
    proof=trial.load(guard);assert proof['all_pass'];trial.check(proof['bindings'])
    protocol=trial.load(trial.OUT/'protocol.json');trial.check(protocol['bindings'])
    assert not (trial.OUT/'process.json').exists(), 'Trial already started; no adoption/retry'
    hard=resource.getrlimit(resource.RLIMIT_AS)[1]
    assert hard==resource.RLIM_INFINITY or hard>=20*2**30
    free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free>=28*2**30
    resource.setrlimit(resource.RLIMIT_AS,(192*2**20,hard))
    bindings=closure([Path(__file__),Path(trial.__file__)]);bindings[str(guard)]=trial.sha(guard);bindings[str(trial.OUT/'protocol.json')]=trial.sha(trial.OUT/'protocol.json')
    trial.check(bindings)
    OUT.mkdir()
    trial.write(OUT/'protocol.json',dict(bindings=bindings,actions=['run','admit','metrics'],
        no_retry_or_adoption=True,run_stage_timeouts='Inner model6h and each audit1h; owner waits for all own children. No external termination of a run owner with an active stage child.',postprocess_stage_timeout_seconds=3600))
    trial.write(OUT/'process.json',dict(pid=os.getpid(),start_stat=Path('/proc/self/stat').read_text(),args=Path('/proc/self/cmdline').read_bytes().decode().strip('\0').split('\0')))
    try:
        trial.check(bindings)
        with (OUT/'run.log').open('x') as log:
            child=subprocess.Popen([sys.executable,str(Path(trial.__file__)),'run'],cwd=trial.R,stdout=log,stderr=subprocess.STDOUT)
            trial.write(OUT/'run_process.json',dict(pid=child.pid,args=child.args,start_stat=Path('/proc',str(child.pid),'stat').read_text()))
            print('CONTINUE FULL CHAIN START run',child.pid,flush=True)
            code=child.wait()
        trial.write(OUT/'run_terminal.json',dict(exit_status=code))
        assert code==0 and trial.gone(trial.OUT), 'Run failed or owner still live; no retry'
        assert trial.load(trial.OUT/'pipeline_terminal.json')['all_stages_completed']
        for action,limit in (('admit',512*2**20),('metrics',8*2**30)):
            trial.check(bindings)
            trial.run_stage(OUT,action,[Path(trial.__file__),action],limit,3600)
        admission=trial.load(trial.OUT/'independent_final_admission_v1.json');metrics=trial.load(trial.OUT/'metrics/verification.json')
        assert admission['all_pass'] and admission['all_primary_coverage_and_isolated_rejection_audits_pass']
        assert metrics['all_pass'] and metrics['independently_checked_metric_sets']==8
        trial.write(OUT/'terminal.json',dict(exit_status=0,full_model_all3audits_closed_admission_and_all8_metrics_completed=True,promoted=False,goal_complete=False))
    except BaseException as error:
        trial.write(OUT/'terminal.json',dict(exit_status=1,error_type=type(error).__name__,error=str(error),no_retry=True))
        raise


if __name__=='__main__':main()
