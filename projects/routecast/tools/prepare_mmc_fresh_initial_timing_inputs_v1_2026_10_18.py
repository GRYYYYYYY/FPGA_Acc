"""Admit fresh per-placement native criticalities without legacy equality claims."""
import json,sys,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from load_initial_connection_criticalities_v2 import load,SCHEMA
from load_design_routing_inputs_v3 import load as design_load
D=R/'experiments/mmc_fresh_initial_timing_inputs_v1_2026-10-18';D.mkdir();S=R/'experiments/mmc_multiplacement_initial_criticality_v1_2026-10-18';ip=S/'independent_verification_v1.json';iv=json.loads(ip.read_text());cp=R/'experiments/fresh_initial_timing_admission_core_v1_2026-10-18/verification.json';core=json.loads(cp.read_text());assert core['status']=='pass' and core['rejections']==16 and iv['status']=='pass';bindings={**iv['bindings'],str(ip):sha(ip),**core['bindings'],str(cp):sha(cp),**closure([Path(__file__)])};g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());before=Path(g['previous_endpoint']);cache=Cache();rows=[]
with cache.installed():
 assert all(sha(p)==h for p,h in bindings.items())
 for case in ['case_01','case_02','case_03']:
  W=D/case;W.mkdir();target=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'demand/endpoints.json';source=S/case/'initial_connection_criticalities.json';payload=W/'initial_connection_criticalities.json';shutil.copyfile(source,payload);assert sha(source)==sha(payload);b={**bindings,str(target):sha(target),str(payload):sha(payload)}
  with (W/'verification.json').open('x') as f:json.dump(dict(schema=SCHEMA,bindings=b,source_case=case,before_endpoint=str(before),after_endpoint=str(target),independent_snapshot_proof=str(ip),routed_connections=115572,nonignored_pin_keys_exactly_manifest=True,fresh_float32_values_and_pin_identities_independently_verified=True,no_target_route_generated=True,source_epoch_sha256=sha(source),scope='Current-placement pre-connection native criticalities; fresh independent TSV/global-pin/f32 proof. Does not claim equality to old criticality values or complete STA/route acceptance.'),f,indent=2)
  fresh=load(W);base=R/'experiments/mmc_multiplacement_feedback_inputs_v1_2026-10-18'/case/'base/verification.json';baseinfo=json.loads(base.read_text());costs,values,extra=design_load(target,base,W,baseinfo['nodes'],baseinfo['scale']);assert dict(fresh)==dict(values) and len(values)==115572;bindings.update(extra);bindings[str(W/'verification.json')]=sha(W/'verification.json');rows.append(dict(case=case,connections=len(values),status='FRESH_INPUTS_AUTHENTICATED'));print('FRESH TIMING INPUT PASS',case,len(values),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all3_fresh_native_timing_and_unchanged_nodebase_inputs_loaded=True,scope='Source admitted inputs only; cached observation production cost separate; no estimator, native target route or timing gain.'),f,indent=2)
