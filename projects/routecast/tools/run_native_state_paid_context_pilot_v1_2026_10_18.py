"""Paid cold old graph initialization followed by one real target local model."""
import json,time,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from class_cached_rc_endpoint_session_v2 import clear_cache,load_endpoints,STATS
from run_native_state_cached_feedback_v1_2026_10_18 import predict
D=R/'experiments/native_state_paid_context_pilot_v1_2026-10-18';D.mkdir(exist_ok=False);old=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json';ep=R/'experiments/xtea_native_state_new_swap_v1_2026-10-18/demand/endpoints.json';inputs=R/'experiments/native_state_feedback_inputs_v1_2026-10-18';ref=R/'experiments/xtea_native_local_compiled_pilot_v2_2026-10-18';prior=ref/'verification.json';v=json.loads(prior.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());bindings={str(p):sha(p) for p in [Path(__file__),old,ep,prior,R/'tools/run_native_state_cached_feedback_v1_2026_10_18.py',R/'tools/class_cached_rc_endpoint_session_v2.py']}
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,order=['cold_old_context','new_target_local_model','exact_parity','independent_audits'],scope='Known graph-template cache integration. Charge cold graph initialization and model continuously, target input authentication remains. Prepared endpoint/staging/timing and native/canonical production excluded explicitly; not a full update or netgain clock.'),f,indent=2);f.write('\n')
clear_cache();start=time.perf_counter();cold=load_endpoints(old);cold_seconds=time.perf_counter()-start;del cold;assert STATS['builds']==1
model_start=time.perf_counter();result=predict(ep,D/'model',inputs/'base/verification.json',inputs/'timing',inputs/'warm','local');model_seconds=time.perf_counter()-model_start;paid_seconds=time.perf_counter()-start;assert STATS['builds']==1 and STATS['hits']==1
for n in ['initial.json','floors.json','round0.json','round1.json','sketch.json']:assert sha(D/'model'/n)==sha(ref/n)
r=json.loads((D/'model/receipt.json').read_text());expected=json.loads((ref/'receipt.json').read_text())
for a,b in zip(r['rounds'],expected['rounds']):assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']}
stages=[]
for stage in ['initial','sketch','events']:
 script=R/'tools'/('verify_native_state_feedback_events_v1_2026_10_18.py' if stage=='events' else 'verify_native_state_feedback_frame_v1_2026_10_18.py');tick=time.perf_counter()
 with (D/(stage+'_audit.log')).open('x') as f:code=subprocess.call([sys.executable,str(script),str(D/'model'),'xtea' if stage=='events' else stage,str(D/(stage+'_audit.json'))],cwd=R,stdout=f,stderr=subprocess.STDOUT)
 stages.append(dict(stage=stage,exit_code=code,seconds=time.perf_counter()-tick))
 if code:raise SystemExit(code)
 print('AUDIT PASS paid context',stage,flush=True)
assert all(sha(p)==h for p,h in bindings.items());bindings[str(D/'model/receipt.json')]=sha(D/'model/receipt.json')
for stage in ['initial','sketch','events']:bindings[str(D/(stage+'_audit.json'))]=sha(D/(stage+'_audit.json'))
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,cache_stats=dict(STATS),cold_initialization_seconds=cold_seconds,model_outer_seconds=model_seconds,continuous_cold_plus_model_seconds=paid_seconds,model_stage_observations={k:x for k,x in r.items() if isinstance(x,(int,float))},all_full_frames_and94events_equal=True,all_three_independent_audits_pass=True,audit_stages=stages,scope='Paid initialization plus one target model, not a continuous entire placement update. Prepared endpoint/staged model/timing and native routing/canonical not inside this clock. Single descriptive observation, no stable speedup or end-to-end gain.'),f,indent=2);f.write('\n')
print('PAID CONTEXT',cold_seconds,model_seconds,paid_seconds,flush=True)
