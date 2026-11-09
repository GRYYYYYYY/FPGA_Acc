"""Freeze one development candidate before model generation; retain complete audit costs."""
import json,sys,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
case=sys.argv[1];assert case=='mmc'
D=R/'experiments/mmc_triangular_span_v9_2026-10-09';assert not D.exists()
control=R/'experiments/ultraembedded_mmc_continuous_workflow_v10_2026-10-09'
admissions=[(R/'experiments/xtea_triangular_span_v9_2026-10-09/verification.json','complete_candidate_physical_and_events_pass'),(control/'verification.json','all_cases_both_complete_arms_authenticated')]
bindings={}
for p,gate in admissions:
 r=json.loads(p.read_text());assert r[gate] and all(sha(k)==h for k,h in r['bindings'].items());bindings[str(p)]=sha(p)
endpoint=control/'seed/demand/mmc/endpoints.json';ep=json.loads(endpoint.read_text());assert len(ep['connections'])==115572
sources=['run_resident_triangular_span_v9.py','verify_resident_demand_frame_physical_v4.py','verify_resident_events_triangular_span_v7.py','verify_triangular_span_candidate_v1.py']
bindings.update(closure([Path(__file__),*[R/'tools'/name for name in sources]]));bindings[str(endpoint)]=sha(endpoint)
D.mkdir();protocol=dict(bindings=bindings,endpoint=str(endpoint),endpoint_sha256=sha(endpoint),policy='Post-hoc development hypothesis: same frozen XTEA-admitted triangular physical span s*(s+1)/2, 50ps unit, two rounds, zero-price exact RC floors and original budgets, ascending wholeNET replacement/retain. No coefficients fitted to MMC labels. Labels read only after complete candidate audits for descriptive matched evaluation; not prospective or strict heldout.',native_labels_read_by_candidate=False,timeout_per_stage_seconds=1200)
(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');model=D/'model';commands=[[sys.executable,R/'tools/run_resident_triangular_span_v9.py',endpoint,model],*[[sys.executable,R/'tools/verify_resident_demand_frame_physical_v4.py',model,frame,model/(frame+'_physical_verification.json')] for frame in ['initial','sketch']],[sys.executable,R/'tools/verify_resident_events_triangular_span_v7.py',model,case,model/'verification.json'],[sys.executable,R/'tools/verify_triangular_span_candidate_v1.py',D,control/'seed/model/mmc']]
stages=[];begin=time.perf_counter()
for index,cmd in enumerate(commands):
 print('START',index,Path(cmd[1]).name,flush=True);tick=time.perf_counter();log=D/f'stage{index}.log'
 with log.open('w') as f:result=subprocess.run([str(x) for x in cmd],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
 stages.append(dict(stage=index,command=[str(x) for x in cmd],log=str(log),seconds=time.perf_counter()-tick,exit_code=result.returncode));(D/'execution_stages.json').write_text(json.dumps(stages,indent=2)+'\n');print('END',index,'exit_code',result.returncode,flush=True)
 if result.returncode:sys.exit(result.returncode)
assert all(sha(k)==h for k,h in bindings.items())
seconds=time.perf_counter()-begin
(D/'execution_receipt.json').write_text(json.dumps(dict(bindings=bindings,files={str(D/'execution_stages.json'):sha(D/'execution_stages.json'),str(D/'verification.json'):sha(D/'verification.json')},continuous_model_and_complete_validation_seconds=seconds,scope='Current model plus independent full frames/events and final candidate admission, all stage/launch/auth costs included. No fresh RR conversion/native/canonical/quality evaluation in this timer; not full workflow gain.'),indent=2)+'\n')
print('COMPLETE model+validation',seconds,flush=True)
