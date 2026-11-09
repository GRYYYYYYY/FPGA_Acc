"""Frozen fullNET schedule control followed by independent full audits."""
import json, sys, subprocess, time, hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
O=R/'experiments/mmc_full_schedule_control_recovery_v1_2026-10-12'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
lineage=O/'source_lineage_v1.json';proof=json.loads(lineage.read_text())
assert all(sha(p)==h for p,h in proof['bindings'].items())
endpoint=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json'
scripts=['run_criticality_multiplicative_full_schedule_v1.py','verify_resident_demand_frame_direct_lattice_v7.py','verify_criticality_multiplicative_full_schedule_v1.py']
bindings={**proof['bindings'],str(lineage):sha(lineage),str(endpoint):sha(endpoint),str(Path(__file__).resolve()):sha(__file__)}
bindings.update({str(R/'tools'/s):sha(R/'tools'/s) for s in scripts})
p=O/'protocol.json';assert not p.exists()
p.write_text(json.dumps(dict(bindings=bindings,connections=115572,nets=55300,rounds=2,scheduling='allNETs sorted each round',costs='acc1/pres1, static span50ps, initialized criticality',seed='same deterministic input/order as affected baseline',timeout_policy='No elapsed-time cancellation; preserve original process',comparison='Historical affected baseline is development evidence, not paired speed proof. Audit initial and round0 parity before attributing round1 differences to scheduling.',scope='Estimator-owned full feedback control; no heldout/native QoR/end-to-end claim'),indent=2)+'\n')
model=O/'model'
stages=[('model',[scripts[0],str(endpoint),str(model)]),('initial_audit',[scripts[1],str(model),'initial',str(model/'initial_physical_verification.json')]),('sketch_audit',[scripts[1],str(model),'sketch',str(model/'sketch_physical_verification.json')]),('event_audit',[scripts[2],str(model),'mmc',str(model/'verification.json')])]
for name,args in stages:
 assert all(sha(p)==h for p,h in bindings.items())
 tick=time.perf_counter();print('FULL SCHEDULE START',name,flush=True)
 with (O/(name+'.log')).open('x') as log:
  code=subprocess.call([sys.executable,str(R/'tools'/args[0]),*args[1:]],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 (O/(name+'_terminal.json')).write_text(json.dumps(dict(exit_status=code,seconds=time.perf_counter()-tick),indent=2)+'\n')
 if code:raise SystemExit(code)
assert all(sha(p)==h for p,h in bindings.items())
(O/'pipeline_terminal.json').write_text(json.dumps(dict(exit_status=0,all_stages_completed=True,scope='Independent audits completed; quality and performance interpretation remains required'),indent=2)+'\n')
print('FULL SCHEDULE PIPELINE COMPLETE',flush=True)
