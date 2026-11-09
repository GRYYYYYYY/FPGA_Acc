"""Serial complete three-case count candidate; no performance interpretation."""
import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/resident_radix_count_complete_v4_2026-10-08'
scripts=['run_resident_soft_demand_radix_count_v4.py','verify_resident_radix_count_parity_v4.py','verify_resident_demand_frame_physical_v3.py','verify_resident_events_round_schedule_cache_v4.py']
bindings=closure([Path(__file__),*[R/'tools'/s for s in scripts]])
cases=[]
for name in ['xtea','8051','mmc']:
 old=R/'experiments/freecores_resident_v1_2026-10-08'/name/'resident' if name!='mmc' else R/'experiments/ultraembedded_mmc_resident_v1_2026-10-08/mmc/resident'
 receipt=old/'receipt.json';r=json.loads(receipt.read_text())
 for section in ['bindings','files']:
  for p,h in r[section].items():assert sha(p)==h
 ep=next(Path(p) for p in r['bindings'] if p.endswith('/endpoints.json'))
 bindings[str(receipt)]=sha(receipt);bindings[str(ep)]=sha(ep)
 cases.append(dict(name=name,endpoint=str(ep)))
D.mkdir(exist_ok=False)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,scope='Serial correctness experiment, complete original endpoints, five full states/all events parity then original independent initial/final Fraction RC and replay audits. No paired runtime or end-to-end gain proof.'),indent=2)+'\n')
rows=[]
for case in cases:
 name=case['name'];out=D/name
 commands=[[scripts[0],case['endpoint'],out],[scripts[1],name,out],[scripts[2],out,'initial'],[scripts[2],out,'sketch'],[scripts[3],out,name,out/'verification.json']]
 for i,args in enumerate(commands):
  assert all(sha(p)==h for p,h in bindings.items())
  with (D/f'{name}_{i}.log').open('w') as log:
   proc=subprocess.run([sys.executable,str(R/'tools'/args[0]),*[str(x) for x in args[1:]]],cwd=R,stdout=log,stderr=subprocess.STDOUT)
  if proc.returncode:
   (D/'failure.json').write_text(json.dumps(dict(case=name,stage=i,exit_code=proc.returncode),indent=2)+'\n')
   raise SystemExit(proc.returncode)
 proofs={}
 for f in ['parity_verification.json','initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
  p=out/f;data=json.loads(p.read_text())
  for section in ['bindings','files']:
   for q,h in data.get(section,{}).items():assert sha(q)==h
  proofs[str(p)]=sha(p)
 rows.append(dict(name=name,status='COMPLETE_CORRECTNESS_VERIFIED',proofs=proofs));print(name,'COMPLETE_CORRECTNESS_VERIFIED',flush=True)
 (D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows),indent=2)+'\n')
