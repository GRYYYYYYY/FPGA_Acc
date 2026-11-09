"""Fresh resource admission and bounded child for the frozen full XTEA comparison."""
import datetime,json,resource,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from observe_neuron_compiled_pipeline_v1 import snapshot
O=R/'experiments/xtea_scaled_present_evaluation_prereg_v1_2026-10-15'
p=json.loads((O/'protocol.json').read_text())
assert all(sha(path)==h for path,h in p['bindings'].items())
for factor in (1,2,4):
 case=R/f'experiments/xtea_scaled_present_factor{factor}_pipeline_v1_2026-10-15'
 assert json.loads((case/'pipeline_terminal.json').read_text())['all_stages_completed']
live=snapshot();reserve=20*2**30
if live['model']['verified_live']:
 lines=Path('/proc/1075109/status').read_text().splitlines()
 vm=int(next(l for l in lines if l.startswith('VmSize:')).split()[1])*1024
 reserve=max(0,20*2**30-vm)
elif live['stages']['model']['terminal']['observed']:reserve=0
free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
required=reserve+9*2**30
admission=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),shared_headroom_bytes=free,required_bytes=required,child_limit_bytes=2**30,remaining_original_model_reservation_bytes=reserve,extra_margin_bytes=8*2**30,admitted=free>=required)
(O/'evaluation_admission.json').write_text(json.dumps(admission,indent=2)+'\n')
if free<required:raise RuntimeError('Comparison not launched: memory admission unavailable')
tick=time.perf_counter()
with (O/'evaluation.log').open('x') as log:
 rc=subprocess.call([sys.executable,str(R/'tools/evaluate_xtea_scaled_present_full_comparison_v1.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_AS,(2**30,2**30)))
(O/'evaluation_terminal.json').write_text(json.dumps(dict(exit_status=rc,seconds=time.perf_counter()-tick))+'\n')
raise SystemExit(rc)
