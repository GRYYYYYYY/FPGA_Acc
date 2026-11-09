"""Single evaluation-only follower for the existing exact wrapper identity.

Never starts or restarts experiments. Missing terminal evidence stops evaluation.
"""
import os,time,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_sequential_group_refinement_v1_2026-10-20'
def startticks(pid):
 try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 except FileNotFoundError:return None
pid=int(sys.argv[1]);ticks=sys.argv[2];assert startticks(pid)==ticks
lock=D/'evaluation_follower.lock';fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
state=D/'evaluation_follower.json'
def save(status,**extra):
 temp=state.with_suffix('.json.tmp');temp.write_text(json.dumps(dict(status=status,pid=os.getpid(),source_wrapper_pid=pid,source_startticks=ticks,**extra),indent=2)+'\n');os.replace(temp,state)
save('WAITING_FOR_ORIGINAL_WRAPPER')
while startticks(pid)==ticks:time.sleep(10)
p=D/'terminal.json'
if not p.exists():save('STOPPED_WRAPPER_GONE_WITHOUT_TERMINAL');sys.exit(1)
t=json.loads(p.read_text())
if len(t['rows'])!=3 or any(c['exit_status']!=0 for c in t['rows']):save('STOPPED_CASE_FAILURE_NO_EVALUATION');sys.exit(1)
save('EVALUATING_ALL6_ADMITTED_ARMS')
with (D/'evaluation.log').open('x') as log:code=subprocess.run([sys.executable,str(R/'tools/evaluate_sequential_group_refinement_v1.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
if code:save('EVALUATION_TERMINAL',exit_status=code);sys.exit(code)
save('INDEPENDENT_METRICS_VERIFYING',evaluation_exit_status=0)
with (D/'independent_metrics.log').open('x') as log:verify=subprocess.run([sys.executable,str(R/'tools/verify_sequential_group_refinement_metrics_v1.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
save('EVALUATION_AND_INDEPENDENT_METRICS_TERMINAL',evaluation_exit_status=0,independent_metrics_exit_status=verify);sys.exit(verify)
