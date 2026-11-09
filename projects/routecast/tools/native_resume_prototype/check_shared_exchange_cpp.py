import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_shared_exchange_cpp_contract_2026-10-07';out.mkdir(exist_ok=False);binary=ROOT/'build/native_resume_shared_exchange_cpp_2026-10-07/exchange'
base=[2026100702,4,4,1,1,0,2,3,4,4,1,2,3,3,10,5,10,5,1,1,1,1,0,0,0,0,0,1,1,0,1,0,7,3,2,0,2]
cases=[('replacement',base,0),('truncated',base[:-1],2),('trailing',base+[99],2),('bad_dest',base[:10]+[9]+base[11:],2),('broken_arc',base[:-2]+[2,0],2)]
rows=[]
for name,values,expected in cases:
 p=out/(name+'.txt');p.write_text(' '.join(map(str,values))+'\n');r=subprocess.run([str(binary),str(p)],capture_output=True,text=True);assert r.returncode==expected,(name,r.stderr);(out/(name+'.stdout')).write_text(r.stdout);(out/(name+'.stderr')).write_text(r.stderr)
 if name=='replacement':
  a=json.loads(r.stdout);assert a['attempts'][0]['accepted'] and a['records'][0]['slots']==[1,3] and a['records'][0]['delay']==10
 rows.append(dict(case=name,exit_code=r.returncode))
(out/'receipt.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
