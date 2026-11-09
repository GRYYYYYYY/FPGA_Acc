"""Frozen objective guard experiment followed by all independent audits."""
import sys,json,time,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
O=R/'experiments/mmc_delayed_history_ablation_v1_2026-10-13'
ep=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json'
scripts=['run_criticality_delayed_history_full_schedule_v1.py','verify_resident_demand_frame_direct_lattice_v7.py','verify_criticality_delayed_history_full_schedule_v1.py']
print('OBJECTIVE GUARD FREEZE START',flush=True)
bindings=closure([Path(__file__),*[R/'tools'/s for s in scripts]])
for proofpath in [O/'preflight_protocol_v1.json',R/'experiments/mmc_net2480_objective_guard_trial_v1_2026-10-12/verification.json']:
 proof=json.loads(proofpath.read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());bindings.update(proof['bindings']);bindings[str(proofpath)]=sha(proofpath)
bindings[str(ep)]=sha(ep)
for v in json.loads(ep.read_text())['inputs'].values():assert sha(v['path'])==v['sha256'];bindings[v['path']]=v['sha256']
assert all(sha(p)==h for p,h in bindings.items())
p=O/'protocol.json';assert not p.exists();p.write_text(json.dumps(dict(bindings=bindings,connections=115572,nets=55300,rounds=2,scheduling='allNETs each round',change='Only initial accumulated overuse addition before round0 skipped; round1 adds round0 overuse once. Objective/overflow guards, search, budgets, initial criticalities, static span and present factor unchanged.',control='mmc_objective_guard_full_schedule_v1_2026-10-12',quality_gate='Same frozen original XML/full channel and spatial metrics after all audits; do not promote solely for objective monotonicity or overflow.',timing_scope='Descriptive historical comparison, not paired speed proof',timeout_policy='No elapsed-time cancellation; preserve original process',scope='Exposed mmc development ablation; native QoR/heldout/end-to-end gain remain unproven'),indent=2)+'\n')
model=O/'model'
stages=[('model',[scripts[0],str(ep),str(model)]),('initial_audit',[scripts[1],str(model),'initial',str(model/'initial_physical_verification.json')]),('sketch_audit',[scripts[1],str(model),'sketch',str(model/'sketch_physical_verification.json')]),('event_audit',[scripts[2],str(model),'mmc',str(model/'verification.json')])]
for name,args in stages:
 assert all(sha(p)==h for p,h in bindings.items());print('OBJECTIVE GUARD START',name,flush=True);tick=time.perf_counter()
 with (O/(name+'.log')).open('x') as log:code=subprocess.call([sys.executable,str(R/'tools'/args[0]),*args[1:]],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 (O/(name+'_terminal.json')).write_text(json.dumps(dict(exit_status=code,seconds=time.perf_counter()-tick),indent=2)+'\n')
 if code:raise SystemExit(code)
assert all(sha(p)==h for p,h in bindings.items())
(O/'pipeline_terminal.json').write_text(json.dumps(dict(exit_status=0,all_stages_completed=True),indent=2)+'\n');print('OBJECTIVE GUARD PIPELINE COMPLETE',flush=True)
