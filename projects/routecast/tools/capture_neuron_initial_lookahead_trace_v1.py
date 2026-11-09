"""Fresh isolated initialized timing capture then independent identity/bit audit."""
import json
import os
import resource
import shutil
import subprocess
import sys
import time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
OUT=R/'experiments/neuron_initial_lookahead_trace_v1_2026-10-17'


def write(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')


def stage(name,args,cwd,env,limit,timeout):
    assert not (OUT/(name+'_process.json')).exists() and not (OUT/(name+'.log')).exists()
    maximum=int(Path('/sys/fs/cgroup/memory.max').read_text());current=int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert maximum-current>=limit+8*2**30
    write(OUT/(name+'_admission.json'),dict(maximum_bytes=maximum,current_bytes=current,child_limit_bytes=limit,margin_bytes=8*2**30))
    started=time.perf_counter();timed_out=False
    with (OUT/(name+'.log')).open('x') as log:
        child=subprocess.Popen(list(map(str,args)),cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_AS,(limit,limit)))
        write(OUT/(name+'_process.json'),dict(pid=child.pid,args=child.args,start_stat=Path('/proc',str(child.pid),'stat').read_text(),address_space_limit_bytes=limit))
        print('INITIAL TIMING START',name,child.pid,flush=True)
        try:code=child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True;child.terminate()
            try:code=child.wait(timeout=30)
            except subprocess.TimeoutExpired:child.kill();code=child.wait()
    write(OUT/(name+'_terminal.json'),dict(exit_status=code,timed_out=timed_out,seconds=time.perf_counter()-started,address_space_limit_bytes=limit))
    assert code==0 and not timed_out,'Failed stage preserved; no retry'


def main():
    build=R/'build/native_initial_lookahead_trace_v1_2026-10-17';receipt=json.loads((build/'receipt.json').read_text());assert sha(build/'sequence_vpr')==receipt['binary_sha256']
    assert all(sha(p)==h for p,h in receipt['bindings'].items())
    prior=R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13';original=prior/'criticality';proof=json.loads((original/'verification.json').read_text());assert proof['nonignored_pin_keys_exactly_manifest']
    command=list(next(x['command'] for x in json.loads((prior/'protocol.json').read_text())['commands'] if x['name']=='criticality'));command[0]=str(build/'sequence_vpr')
    bindings=closure([Path(__file__),R/'tools/verify_neuron_initial_timing_v1.py',R/'tools/verify_neuron_initial_lookahead_v1.py',R/'tools/verify_neuron_initial_lookahead_trace_v1.py']);bindings.update(receipt['bindings'])
    for p in (build/'receipt.json',build/'sequence_vpr',prior/'protocol.json',original/'verification.json',original/'criticality.tsv',original/'initial_connection_criticalities.json'):
        bindings[str(p)]=sha(p)
    for option in ('--read_rr_graph','--sdc_file'):
        bindings[command[command.index(option)+1]]=sha(command[command.index(option)+1])
    bindings[command[1]]=sha(command[1])
    assert int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())>=28*2**30
    OUT.mkdir();work=OUT/'work';work.mkdir()
    for name in ('design.blif','design.net','design.place'):
        source=original/name;target=work/name;shutil.copyfile(source,target);bindings[str(source)]=sha(source);bindings[str(target)]=sha(target);assert bindings[str(source)]==bindings[str(target)]
    write(OUT/'protocol.json',dict(bindings=bindings,command=command,working_directory=str(work),native_limit_bytes=20*2**30,native_timeout_seconds=1800,verifier_limit_bytes=512*2**20,
        expected_all_cluster_sink_pins=92608,expected_nonignored_CIDs=77106,phase='Same first native criticality getter as certified snapshot; exit before returning to its caller.',policy='Independent read-only atom/slack metadata; original C criticality bytes must match. No source/vendor or historic binary mutation, no connection budget/constraints fitting, no final route label/QoR/performance claim.',heldout=False,promoted=False))
    write(OUT/'process.json',dict(pid=os.getpid(),start_stat=Path('/proc/self/stat').read_text(),args=Path('/proc/self/cmdline').read_bytes().decode().strip('\0').split('\0')))
    try:
        env=os.environ.copy();env['ROUTECAST_LOOKAHEAD_TRACE']=str(work/'lookahead_trace.tsv');env['ROUTECAST_INITIAL_LOOKAHEAD_DELAY']=str(work/'lookahead_delay.tsv');env['ROUTECAST_INITIAL_TIMING']=str(work/'timing.tsv');env['ROUTECAST_INITIAL_CRITICALITY']=str(work/'criticality.tsv')
        stage('native',command,work,env,20*2**30,1800)
        # Keep native stdout in its capture directory for explicit audit bindings.
        shutil.copyfile(OUT/'native.log',work/'native.log')
        stage('verification',[sys.executable,R/'tools/verify_neuron_initial_timing_v1.py',OUT],R,os.environ.copy(),512*2**20,600)
        assert json.loads((OUT/'verification.json').read_text())['all_pass']
        stage('lookahead_verification',[sys.executable,R/'tools/verify_neuron_initial_lookahead_v1.py',OUT],R,os.environ.copy(),512*2**20,600)
        assert json.loads((OUT/'lookahead_verification.json').read_text())['all_pass']
        stage('trace_verification',[sys.executable,R/'tools/verify_neuron_initial_lookahead_trace_v1.py',OUT],R,os.environ.copy(),512*2**20,600)
        assert json.loads((OUT/'trace_verification.json').read_text())['all_pass']
        assert all(sha(p)==h for p,h in bindings.items())
        write(OUT/'terminal.json',dict(exit_status=0,initialized_timing_capture_and_full_independent_audit_pass=True,new_model_or_final_native_route=False))
    except BaseException as error:
        write(OUT/'terminal.json',dict(exit_status=1,error_type=type(error).__name__,error=str(error),no_retry=True));raise


if __name__=='__main__':main()
