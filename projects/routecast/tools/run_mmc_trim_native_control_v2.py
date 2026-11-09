"""One predeclared corrected no-estimator control; preserve the failed predecessor."""
import json,os,sys,time,shutil,subprocess,resource
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
P=R/'experiments/mmc_native_seed_utility_pilot_v1_2026-10-18/protocol.json'
F=R/'experiments/mmc_trim_metadata_repair_v2_2026-10-21/verification.json'
p=json.loads(P.read_text());f=json.loads(F.read_text())
assert f['physical_paths_exact'] and f['all_non_coordinate_text_identical']
assert all(sha(k)==v for d in [p,f] for k,v in d['bindings'].items())
D=R/'experiments/mmc_trim_native_control_v2_2026-10-21';D.mkdir();N=D/'native';N.mkdir()
src=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/mmc'
for name in ['design.blif','design.net','design.place']:shutil.copyfile(src/name,N/name)
seed=F.parent/'seed.route';bindings={**p['bindings'],**f['bindings'],str(P):sha(P),str(F):sha(F),str(Path(__file__)):sha(__file__),str(R/'tools/audit_mmc_trim_native_control_v2.py'):sha(R/'tools/audit_mmc_trim_native_control_v2.py')}
protocol={'bindings':bindings,'commands':{'trim':p['commands']['trim']},'seed':str(seed),'budget':{'native_calls':1,'AS_GiB':32,'core_bytes':0,'elapsed_timeout':None,'workers':1,'seed':1,'width':128,'max_router_iterations':100},'scope':'Corrected no-estimator trim control. Previously exposed same MMC placement, fixed order after historical raw/local; not randomized paired timing. All setup/model/native/gate costs remain separate; no full workflow or unseen admission.'}
(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
def limits():
 resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
assert int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())>40*2**30
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_NATIVE_SEED']=str(seed)
print('TRIM V2 NATIVE START',flush=True);t=time.perf_counter()
with (N/'native.log').open('x') as log:
 code=subprocess.run(p['commands']['trim'],cwd=N,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits).returncode
terminal={'arm':'trim_v2','exit_status':code,'native_timeout':False,'native_process_seconds':time.perf_counter()-t}
(N/'terminal.json').write_text(json.dumps(terminal)+'\n');print(json.dumps(terminal),flush=True)
assert all(sha(k)==v for k,v in bindings.items())
if code:raise SystemExit(code)
raise SystemExit(subprocess.run([sys.executable,str(R/'tools/audit_mmc_trim_native_control_v2.py')],cwd=R).returncode)
