"""Frozen online model plus complete physical/fallback event audits, no labels."""
import json,sys,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_actual_old_joint_fallback_linear_v11_2026-10-09';assert not D.exists()
B=R/'experiments/ultraembedded_mmc_continuous_workflow_v10_2026-10-09'
sources=['run_resident_actual_old_joint_fallback_linear_v11.py','verify_resident_demand_frame_physical_v4.py','verify_resident_events_actual_old_joint_fallback_linear_v9.py']
bindings=closure([Path(__file__),*[R/'tools'/s for s in sources]])
for p,gate in [(R/'experiments/xtea_actual_old_joint_fallback_linear_v11_2026-10-09/verification.json','no_fallback_XTEA_full_state_parity_and_complete_physical_event_checks_pass'),(R/'experiments/fallback_event_auditor_contract_v1_2026-10-09/verification.json','all_pass'),(B/'verification.json','all_cases_both_complete_arms_authenticated')]:
 proof=json.loads(p.read_text());assert proof[gate]
 for file,h in proof['bindings'].items():assert sha(file)==h;bindings[file]=h
 bindings[str(p)]=sha(p)
endpoint=B/'seed/demand/mmc/endpoints.json';bindings[str(endpoint)]=sha(endpoint)
D.mkdir();(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,endpoint=str(endpoint),endpoint_sha256=sha(endpoint),policy='Post-hoc development online feedback. Same original linear span/50ps/2 rounds as admitted control. Primary failure invokes current-old/replayed-primary joint candidates, 10000 states, strict actual-old union objective decrease, wholeNET commit/retain. New round ledger/prices/affected schedule recomputed. No native labels or archived round candidates. All query physical/RC/ledger/epoch/fallback audits paid. Not full workflow timing or heldout.',timeout_per_stage_seconds=1200),indent=2)+'\n')
model=D/'model';commands=[[sys.executable,R/'tools'/sources[0],endpoint,model],*[[sys.executable,R/'tools'/sources[1],model,frame,model/(frame+'_physical_verification.json')] for frame in ('initial','sketch')],[sys.executable,R/'tools'/sources[2],model,'mmc',model/'verification.json']]
begin=time.perf_counter();stages=[]
for i,cmd in enumerate(commands):
 print('START',i,Path(cmd[1]).name,flush=True);tick=time.perf_counter();log=D/f'stage{i}.log'
 with log.open('w') as f:result=subprocess.run([str(v) for v in cmd],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
 stages.append(dict(stage=i,command=[str(v) for v in cmd],seconds=time.perf_counter()-tick,exit_code=result.returncode,log=str(log)));(D/'stages.json').write_text(json.dumps(stages,indent=2)+'\n');print('END',i,result.returncode,flush=True)
 if result.returncode:sys.exit(result.returncode)
audit=json.loads((model/'verification.json').read_text());assert audit['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and audit['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass'] and audit['completed']==115572 and audit['fallback_calls']>0
for name in ('initial.json','floors.json'):
 a=model/name;b=B/'seed/model/mmc'/name;assert json.loads(a.read_text())==json.loads(b.read_text());bindings[str(a)]=sha(a);bindings[str(b)]=sha(b)
for p in [model/'verification.json',model/'initial_physical_verification.json',model/'sketch_physical_verification.json',D/'stages.json']:bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
r=dict(bindings=bindings,complete_online_feedback_physical_and_actual_old_fallback_events_pass=True,initial_floors_equal_control=True,fallback_calls=audit['fallback_calls'],fallback_accepted=audit['fallback_accepted'],fallback_retained=audit['fallback_retained'],overflow_units=audit['overflow_units'],continuous_model_and_complete_validation_seconds=time.perf_counter()-begin,scope='Full online feedback and original XML/Fraction physical/event validation only. No conversion/native/QoR/hotspot/heldout/full workflow gain evidence.')
(D/'verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='bindings'},indent=2),flush=True)
