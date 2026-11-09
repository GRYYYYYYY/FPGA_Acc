"""Exact full-trajectory parity and unchanged independent audits; no speed inference."""
import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));from pre_route_endpoints import sha
D=R/'experiments/xtea_native_local_compiled_pilot_v2_2026-10-18';ref=R/'experiments/xtea_native_state_feedback_comparison_v3_2026-10-18/local';r=json.loads((D/'receipt.json').read_text());old=json.loads((ref/'receipt.json').read_text());files=['initial.json','floors.json','round0.json','round1.json','sketch.json']
for name in files:assert sha(D/name)==sha(ref/name),name
for a,b in zip(r['rounds'],old['rounds']):assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']}
for stage in ['initial','sketch','events']:
 script=R/'tools'/('verify_native_state_feedback_events_v1_2026_10_18.py' if stage=='events' else 'verify_native_state_feedback_frame_v1_2026_10_18.py')
 with (D/(stage+'_audit.log')).open('x') as f:code=subprocess.call([sys.executable,str(script),str(D),'xtea' if stage=='events' else stage,str(D/(stage+'_audit.json'))],cwd=R,stdout=f,stderr=subprocess.STDOUT)
 if code:raise SystemExit(code)
 print('AUDIT PASS compiled local',stage,flush=True)
bindings={str(Path(__file__)):sha(__file__),str(ref/'receipt.json'):sha(ref/'receipt.json'),str(D/'receipt.json'):sha(D/'receipt.json')}
for name in files+['initial_audit.json','sketch_audit.json','events_audit.json']:bindings[str(D/name)]=sha(D/name)
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,all_full_frames_byte_identical=True,all94events_equal_excluding_timing_and_output_path=True,all_three_original_XML_fraction_audits_pass=True,current_stage_observations={k:v for k,v in r.items() if isinstance(v,(int,float))},reference_stage_observations={k:v for k,v in old.items() if isinstance(v,(int,float))},scope='Known compiled kernel/price-store integration in native-state local update. One unpaired component observation, no stable speedup or end-to-end gain. No native rerun necessary because all frames/transactions equal previously audited native input.'),f,indent=2);f.write('\n')
