"""Frozen full two-case within/across direction-pressure development cohort."""
import json,sys,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/freecores_direction_pressure_model_v2_2026-10-08';D.mkdir()
runner=R/'tools/run_resident_direction_pressure_pool_v1.py';auditor=R/'tools/verify_resident_direction_pressure_events_v1.py'
bindings=closure([Path(__file__),runner,auditor,R/'tools/verify_resident_demand_frame_physical_v3.py',R/'tools/select_resident_native_seed_subset_v1.py'])
component=R/'experiments/freecores_direction_pressure_component_v1_2026-10-08/verification.json';cp=json.loads(component.read_text());assert all(sha(k)==h for k,h in cp['bindings'].items());bindings[str(component)]=sha(component);bindings.update(cp['bindings'])
pr=R/'experiments/freecores_prospective_evaluation_prereg_v1_2026-10-08/protocol.json';p=json.loads(pr.read_text());assert all(sha(k)==h for k,h in p['bindings'].items());bindings[str(pr)]=sha(pr)
endpoints={};commands={}
for name in ['8051','xtea']:
 ep=R/'experiments/freecores_native_demand_v1_2026-10-08'/name/'endpoints.json';endpoints[name]=ep;d=json.loads(ep.read_text());bindings[str(ep)]=sha(ep)
 for v in d['inputs'].values():bindings[v['path']]=v['sha256']
 receipt=R/'experiments/freecores_native_cold_v1_2026-10-08'/name/'receipt.json';bindings[str(receipt)]=sha(receipt);nativeprotocol=receipt.with_name('protocol.json');bindings[str(nativeprotocol)]=sha(nativeprotocol);commands[name]=json.loads(nativeprotocol.read_text())['command']
protocol=dict(bindings=bindings,cases=['8051','xtea'],model_order=['xtea','8051'],modes=['within_polarity','across_polarity'],timeout_seconds=1200,rounds=2,metrics=p['metrics'],native_reference_commands=commands,scope='Known-label development pressure-polarity control, not topology-direction erasure or unseen/prospective claim. Both modes remove track resolution; within retains polarity, across merges it at identical type/full bbox/layer/segment/capacity/RC. Complete original floors/RC budgets/graph/endpoints and two50ps rounds; independent projected price deltas determine affected NET closure. All positive CHAN metrics and same fixed cold labels; later unchanged whole-NET selection/native/FULL/canonical/ignored gates needed, failures retained. No fitted parameter, omitted query, FIFO reduction or best arm/round label choice.')
assert all(sha(k)==h for k,h in bindings.items());(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for name in protocol['model_order']:
 for mode in protocol['modes']:
  dest=D/name/mode/'resident';dest.parent.mkdir(parents=True);tick=time.perf_counter()
  try:
   with (dest.parent/'model.log').open('w') as f:r=subprocess.run([sys.executable,str(runner),str(endpoints[name]),str(dest),mode],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
   assert r.returncode==0,r.returncode;assert all(sha(k)==h for k,h in bindings.items())
   row=dict(name=name,mode=mode,status='MODEL_OUTPUT_PENDING_AUDITS',elapsed_seconds=time.perf_counter()-tick)
  except Exception as error:
   rows.append(dict(name=name,mode=mode,status='FAILED_OR_TIMEOUT',error=repr(error),elapsed_to_failure_seconds=time.perf_counter()-tick));(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');raise
  rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(row,flush=True)
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Four complete model producers, not scientific audit or performance certification.'),indent=2)+'\n')
