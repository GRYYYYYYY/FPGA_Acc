"""XTEA no-fallback integration parity and complete physical/event audits."""
import json,sys,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/xtea_actual_old_joint_fallback_linear_v11_2026-10-09';assert not D.exists()
B=R/'experiments/xtea_resident_native_handoff_v1_2026-10-09'
bindings=closure([Path(__file__),R/'tools/run_resident_actual_old_joint_fallback_linear_v11.py'])
for proof,gate in [(B/'verification.json','complete_model_frames_and_events_equal'),(R/'experiments/resident_actual_old_fallback_adapter_v1_2026-10-09/verification.json','all_pass')]:
 x=json.loads(proof.read_text());assert x[gate]
 for p,h in x['bindings'].items():assert sha(p)==h;bindings[p]=h
 bindings[str(proof)]=sha(proof)
p=json.loads((B/'model/receipt.json').read_text());endpoint=next(Path(k) for k in p['bindings'] if k.endswith('/endpoints.json'));assert sha(endpoint)==p['bindings'][str(endpoint)];bindings[str(endpoint)]=sha(endpoint)
D.mkdir();(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,endpoint=str(endpoint),policy='Fresh online model, original linear control span/50ps/2 rounds. Current-old fallback only for primary failure. No native labels. XTEA parity admits no-fallback branch only; no claim for MMC recovery.'),indent=2)+'\n')
model=D/'model';commands=[[sys.executable,R/'tools/run_resident_actual_old_joint_fallback_linear_v11.py',endpoint,model],*[[sys.executable,R/'tools/verify_resident_demand_frame_physical_v4.py',model,frame,model/(frame+'_physical_verification.json')] for frame in ('initial','sketch')],[sys.executable,R/'tools/verify_resident_events_actual_old_joint_fallback_linear_v9.py',model,'xtea',model/'verification.json']]
stages=[]
for i,command in enumerate(commands):
 print('START',i,Path(command[1]).name,flush=True);tick=time.perf_counter();log=D/f'stage{i}.log'
 with log.open('w') as f:result=subprocess.run([str(v) for v in command],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
 stages.append(dict(stage=i,exit_code=result.returncode,seconds=time.perf_counter()-tick,log=str(log)));(D/'stages.json').write_text(json.dumps(stages,indent=2)+'\n');print('END',i,result.returncode,flush=True)
 if result.returncode:sys.exit(result.returncode)
r=json.loads((model/'receipt.json').read_text());assert not any('fallback' in e for rr in r['rounds'] for e in rr['events'])
for name in ('initial.json','floors.json','round0.json','round1.json','sketch.json'):
 a=model/name;b=B/'model'/name;assert json.loads(a.read_text())==json.loads(b.read_text()),name;bindings[str(a)]=sha(a);bindings[str(b)]=sha(b)
assert all(sha(p)==h for p,h in bindings.items())
proof=dict(bindings=bindings,no_fallback_XTEA_full_state_parity_and_complete_physical_event_checks_pass=True,scope='XTEA original successful-search branch equivalence only. No nonzero online fallback, MMC quality or complete native runtime gain proof.')
(D/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='bindings'},indent=2),flush=True)
