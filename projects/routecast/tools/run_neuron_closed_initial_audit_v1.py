"""Audit only an immutable closed initial snapshot when shared memory permits."""
import json
import resource
import subprocess
import sys
import time
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]

def main():
    out=R/'experiments/neuron_closed_initial_frame_v1_2026-10-13'
    capture=json.loads((out/'frame_capture.json').read_text())
    assert not capture['full_model_terminal_proven']
    assert all(sha(p)==h for p,h in capture['files'].items())
    pid=capture['source_model_pid_observed_live'];proc=Path(f'/proc/{pid}/status')
    reserve=0
    if proc.exists():
        lines=proc.read_text().splitlines()
        vms=int(next(line.split()[1] for line in lines if line.startswith('VmSize:')))*1024
        reserve=max(0,24*2**30-vms)
    maximum=int(Path('/sys/fs/cgroup/memory.max').read_text());current=int(Path('/sys/fs/cgroup/memory.current').read_text())
    cap=8*2**30;required=cap+8*2**30+reserve
    if maximum-current<required:
        print(json.dumps(dict(audit_launched=False,reason='insufficient shared headroom after reserving live model allowance',available=maximum-current,required=required)),flush=True)
        return
    script=R/'tools/verify_closed_initial_frame_direct_lattice_v1.py'
    def bound():resource.setrlimit(resource.RLIMIT_AS,(cap,cap))
    tick=time.perf_counter()
    with (out/'initial_audit.log').open('x') as log:
        code=subprocess.call([sys.executable,str(script),str(out),'initial',str(out/'initial_physical_verification.json')],cwd=R,stdout=log,stderr=subprocess.STDOUT,preexec_fn=bound)
    (out/'initial_audit_terminal.json').write_text(json.dumps(dict(exit_status=code,seconds=time.perf_counter()-tick,address_space_limit_bytes=cap))+'\n')
    if code:raise SystemExit(code)
    print('CLOSED INITIAL INDEPENDENT FRAME AUDIT PASS; FULL MODEL STILL SEPARATE',flush=True)

if __name__=='__main__':main()
