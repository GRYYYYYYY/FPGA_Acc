"""Compose actual control/ready preedge records to isolate early unknown input."""
import json,hashlib,itertools
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_ibus_ready_capture_path_v1_2026-10-09';D.mkdir(exist_ok=True)
C=R/'experiments/full_ibus_ready_control_preedge_trace_v1_2026-10-09/trace_audit.json';T=R/'experiments/full_ibus_ready_preedge_trace_v1_2026-10-09/trace_audit.json';L=R/'experiments/full_ibus_ready_control_export_luts_v1_2026-10-09/audit.json';c=json.loads(C.read_text());t=json.loads(T.read_text());assert c['replay_fidelity'] and t['replay_fidelity'];mask=next(r['mask'] for r in json.loads(L.read_text())['records'] if r['node']=='new_n6085')
for b in [0,1]:assert mask[-1-(1+(b<<3)+(1<<4))]==str(b)
controlcycles=[];readycycles=[];unknowncycles=[]
for r,p in zip(c['rows'],t['rows']):
 assert r['cycle']==p['cycle'];cy=r['cycle']
 if [r[x] for x in ['new_n6111','new_n6086','new_n6107','new_n6109']]==['1','0','0','1']:
  assert p['native_ready_pins'][::-1][1]==r['new_n6108'];controlcycles.append(cy)
  pins=p['native_ready_pins'][::-1]
  if pins[0]=='0' and pins[2:4]=='01':
   assert p['native_ready']==r['new_n6108'];readycycles.append(cy)
   if p['native_ready']=='x':unknowncycles.append(cy)
assert 5 in unknowncycles
out={'control_equals_capture_cycles':controlcycles,'ready_equals_capture_cycles':readycycles,'isolated_unknown_cycles':unknowncycles,'first_witness':{'control':c['rows'][5],'ready':t['rows'][5]},'scope':'Actual observed other control6085inputs allknown permitting capture6108, plus actual earlyready context masks tagerror. Capture is sole unknown at control6085 for these cycles; upstreamcapture can have multiple causes. Earlier counterhigh-to5938/capture evidence separate; does not explain laterunknowns or all42370 mismatches.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [C,T,L]}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'control_cycles':len(controlcycles),'ready_cycles':len(readycycles),'isolated_unknown_cycles':len(unknowncycles),'first':unknowncycles[0]},indent=2))
