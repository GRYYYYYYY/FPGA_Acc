"""Wait original replay, independently audit, then summarize; never restart jobs."""
import json,sys,time,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));from pre_route_endpoints import sha
O=R/'experiments/mmc_native_snapshot_present_pair_v1_2026-10-10';pid=1377274
sources=[Path(__file__),R/'tools/verify_native_snapshot_present_pair_v1.py',R/'tools/summarize_native_snapshot_present_pair_v1.py'];bindings={str(p.resolve()):sha(p) for p in sources}
f=O/'pipeline_startup_v1.json';assert not f.exists();f.write_text(json.dumps({'bindings':bindings,'replay_pid':pid},indent=2)+'\n');missing=0
while not (O/'receipt.json').exists():
 result=subprocess.run(['ps','-p',str(pid),'-o','args='],capture_output=True,text=True)
 live='replay_native_snapshot_present_pair_v1.py' in result.stdout;missing=0 if live else missing+1
 if missing>=3:raise RuntimeError('original replay absent three polls without receipt; preserved, not restarted')
 time.sleep(10)
assert all(sha(p)==h for p,h in bindings.items())
for name,script in [('audit','verify_native_snapshot_present_pair_v1.py'),('summary','summarize_native_snapshot_present_pair_v1.py')]:
 print('PAIR PIPELINE START',name,flush=True)
 with (O/(name+'.log')).open('w') as log:status=subprocess.run([sys.executable,str(R/'tools'/script)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 (O/(name+'_terminal_v1.json')).write_text(json.dumps({'exit_status':status},indent=2)+'\n')
 if status:raise RuntimeError(name+' failed; no next stage admission')
 assert all(sha(p)==h for p,h in bindings.items())
print('PAIR PIPELINE COMPLETE',flush=True)
