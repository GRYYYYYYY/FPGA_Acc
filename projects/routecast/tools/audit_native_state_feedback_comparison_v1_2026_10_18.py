"""Run all original-XML/Fraction frame and full event audits for frozen arms."""
import json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));from pre_route_endpoints import sha
D=R/'experiments/xtea_native_state_feedback_comparison_v3_2026-10-18';O=R/'experiments/native_state_feedback_audits_v1_2026-10-18';O.mkdir(exist_ok=False);stages=[];start=time.perf_counter()
for arm in ['all','local']:
 for stage in ['initial','sketch','events']:
  out=D/arm;proof=O/(arm+'_'+stage+'.json');script='verify_native_state_feedback_events_v1_2026_10_18.py' if stage=='events' else 'verify_native_state_feedback_frame_v1_2026_10_18.py';args=[str(out),'xtea' if stage=='events' else stage,str(proof)];tick=time.perf_counter()
  with (O/(arm+'_'+stage+'.log')).open('x') as f:code=subprocess.call([sys.executable,str(R/'tools'/script),*args],cwd=R,stdout=f,stderr=subprocess.STDOUT)
  row=dict(arm=arm,stage=stage,exit_code=code,seconds=time.perf_counter()-tick);stages.append(row)
  with (O/(arm+'_'+stage+'_terminal.json')).open('x') as f:json.dump(row,f);f.write('\n')
  if code:raise SystemExit(code)
  print('AUDIT PASS',arm,stage,flush=True)
files=[Path(__file__),D/'receipt.json',R/'tools/verify_native_state_feedback_events_v1_2026_10_18.py',R/'tools/verify_native_state_feedback_frame_v1_2026_10_18.py'];files.extend(O.glob('all_*.json'));files.extend(O.glob('local_*.json'))
with (O/'verification.json').open('x') as f:json.dump(dict(bindings={str(p):sha(p) for p in files},stages=stages,all_six_original_XML_fraction_audits_pass=True,audit_driver_seconds=time.perf_counter()-start,scope='Frame and complete transaction audits; no target native routing, heldout, physical commit or netgain claim.'),f,indent=2);f.write('\n')
