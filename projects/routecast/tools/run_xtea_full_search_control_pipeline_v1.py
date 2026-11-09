"""Full second-design portability experiment and unchanged independent auditors."""
import json,sys,time,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1]
O=R/'experiments/xtea_design_scoped_full_search_control_v1_2026-10-13';O.mkdir()
ep=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json'
base=R/'experiments/xtea_retained_node_base_v1_2026-10-13/verification.json'
crit=R/'experiments/xtea_retained_native_inputs_v1_2026-10-13/criticality'
model=O/'model';scripts=['run_design_scoped_full_search_control_v1.py','verify_resident_demand_frame_direct_lattice_v7.py','verify_criticality_delayed_history_full_schedule_v1.py']
bindings=closure([Path(__file__),*[R/'tools'/s for s in scripts]])
for p in [base.with_name('independent_verification.json'),R/'experiments/retained_tree_cross_design_readiness_v1_2026-10-13/full_search_control_derivation_v1.json']:
 v=json.loads(p.read_text());assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
(O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,endpoint=str(ep),node_base_proof=str(base),criticality_directory=str(crit),connections=2450,nets=1448,rounds=2,heldout=False,policy='Original full-search primary, no retained seeding, delayed history, fixed per-pin initial criticality, wholeNET fallback, exact objective and overflow admission.',scope='Complete exposed XTEA input/model portability and correctness validation; no accuracy selection, heldout family, native QoR or paired speed proof.'),indent=2)+'\n')
stages=[('model',[scripts[0],str(ep),str(model),str(base),str(crit)]),('initial_audit',[scripts[1],str(model),'initial',str(model/'initial_physical_verification.json')]),('sketch_audit',[scripts[1],str(model),'sketch',str(model/'sketch_physical_verification.json')]),('event_audit',[scripts[2],str(model),'xtea',str(model/'verification.json')])]
for name,args in stages:
 assert all(sha(p)==h for p,h in bindings.items());print('XTEA START',name,flush=True);tick=time.perf_counter()
 with (O/(name+'.log')).open('x') as log:code=subprocess.call([sys.executable,str(R/'tools'/args[0]),*args[1:]],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 (O/(name+'_terminal.json')).write_text(json.dumps(dict(exit_status=code,seconds=time.perf_counter()-tick))+'\n')
 if code:raise SystemExit(code)
assert all(sha(p)==h for p,h in bindings.items())
(O/'pipeline_terminal.json').write_text(json.dumps(dict(exit_status=0,all_stages_completed=True))+'\n')
print('XTEA full model and independent audits PASS',flush=True)
