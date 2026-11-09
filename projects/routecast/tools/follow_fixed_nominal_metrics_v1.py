"""Wait only for the existing evaluation owner, then independently verify metrics."""
import json,os,time,sys,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'
def ticks(pid):
 try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 except FileNotFoundError:return None
pid=int(sys.argv[1]);start=sys.argv[2];assert ticks(pid)==start
script=R/'tools/verify_fixed_nominal_ablation_metrics_v1.py';digest=hashlib.sha256(script.read_bytes()).hexdigest();state=D/'independent_metrics_follower.json';lock=D/'independent_metrics_follower.lock';fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
def save(status,**extra):
 p=state.with_suffix('.json.tmp');p.write_text(json.dumps(dict(status=status,pid=os.getpid(),evaluation_owner_pid=pid,evaluation_owner_startticks=start,verifier=str(script),verifier_sha256=digest,**extra),indent=2)+'\n');os.replace(p,state)
save('WAITING_FOR_ORIGINAL_EVALUATION_OWNER')
while ticks(pid)==start:time.sleep(10)
source=json.loads((D/'evaluation_follower.json').read_text())
if source['status']!='EVALUATION_TERMINAL' or source['exit_status']!=0:save('STOPPED_WITHOUT_SUCCESSFUL_EVALUATION');sys.exit(1)
assert hashlib.sha256(script.read_bytes()).hexdigest()==digest
save('INDEPENDENT_METRICS_VERIFYING')
with (D/'independent_metrics.log').open('x') as log:code=subprocess.run([sys.executable,str(script)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
save('INDEPENDENT_METRICS_TERMINAL',exit_status=code);sys.exit(code)
