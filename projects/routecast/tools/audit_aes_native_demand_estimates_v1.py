import json,subprocess,sys
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
name=sys.argv[1];assert name in ['aes_cipher','aes_inv_cipher'];root=R/'experiments/aes_native_demand_estimates_v1_2026-10-08';data=json.loads((root/'receipt.json').read_text());assert all(x['exit_code']==0 for x in data['rows']);assert all(sha(k)==v for k,v in data['bindings'].items());out=root/name/'resident';commands=[[sys.executable,str(R/'tools/verify_resident_demand_frame_physical_v3.py'),str(out),frame] for frame in ['initial','sketch']];commands.append([sys.executable,str(R/'tools/verify_aes_native_demand_feedback_owner_sets_v1.py'),name])
for i,cmd in enumerate(commands):
 with (root/name/f'independent_audit_{i}.log').open('w') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=180,check=True)
 print(name,'AUDIT',i,'PASS',flush=True)
