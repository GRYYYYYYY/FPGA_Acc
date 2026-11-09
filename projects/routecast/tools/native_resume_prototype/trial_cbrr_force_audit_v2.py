"""Observe actual setter/consumer slot values without changing decisions."""
import json,os,shutil,subprocess,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];build=ROOT/'build/native_resume_cbrr_force_audit_v2_2026-10-07';binary=build/'routecast_resume_vpr';br=json.loads((build/'receipt.json').read_text());assert sha(binary)==br['binary_sha256']
out=ROOT/'experiments/native_resume_cbrr_force_audit_v2_2026-10-07';out.mkdir(exist_ok=False)
bindings={str(build/'receipt.json'):sha(build/'receipt.json'),str(binary):sha(binary),str(Path(__file__)):sha(Path(__file__))};tasks=[]
for w,i in ((16,1),(32,3)):
 for mode in ('workflow','cold'):
  base=ROOT/f'experiments/native_resume_cbrrfix_w{w}_m{i}_{mode}_2026-10-07';r=json.loads((base/'receipt.json').read_text());p=json.loads((base/'protocol.json').read_text());assert r['protocol_sha256']==sha(base/'protocol.json')
  native=next(s['native'] for s in r['stages'] if 'native' in s);cmd=[str(binary),*native['command'][1:]]
  files=[(Path(f),name) for f,name in ((next(f for f in p['inputs'] if f.endswith('/design.blif')),'design.blif'),(next(f for f in p['inputs'] if f.endswith('/design.net')),'design.net'),(next(f for f in p['inputs'] if f.endswith('/target.place')),'design.place'))]
  for f,name in files:assert sha(f)==p['inputs'][str(f)];bindings[str(f)]=sha(f)
  for f in (base/'first/output.route',base/'first_seed.route') if mode=='workflow' else (base/'first/output.route',):bindings[str(f)]=sha(f)
  tasks.append(dict(width=w,index=i,mode=mode,base=str(base),command=cmd,files=[(str(f),n) for f,n in files]))
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,tasks=tasks,scope='Instrumentation only, two fixed timing-failure cases plus their cold controls. No decision/index repair or performance comparison; failure retained.'),indent=2)+'\n');rows=[]
norm=lambda f:{n:Counter(ps) for n,ps in physical_paths(f).items() if ps}
for task in tasks:
 w,i,mode=task['width'],task['index'],task['mode'];base=Path(task['base']);work=out/f'w{w}_m{i}_{mode}';work.mkdir()
 for f,name in task['files']:shutil.copyfile(f,work/name)
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_CBRR_GROWTH_AUDIT']='1';env['ROUTECAST_CBRR_FORCE_AUDIT']='1'
 if mode=='workflow':env.update(ROUTECAST_RESUME_SAME_PLACE_ROUTE=str(base/'first_seed.route'),ROUTECAST_RESUME_ALLOW_PARTIAL='1')
 with (work/'run.log').open('w') as stream:code=subprocess.run(task['command'],cwd=work,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
 text=(work/'run.log').read_text();assert code==0 and 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
 assert norm(work/'output.route')==norm(base/'first/output.route')
 events=[line.split() for line in text.splitlines() if line.startswith(('RC_GROWTH','RC_FORCE'))]
 assert events and events[0][0]=='RC_GROWTH_INIT'
 row=dict(width=w,index=i,mode=mode,exit_code=code,paths_equal_original=True,events=events,files={str(f):sha(f) for f in work.iterdir() if f.is_file()})
 rows.append(row);(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n');print(row['width'],row['index'],mode,len(events),flush=True)
assert all(sha(f)==h for f,h in bindings.items())
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),rows=rows,scope='Growth audit with unchanged final paths; prior proofs reused by path identity. Only reached timing-update blocks logged; no performance measurement.'),indent=2)+'\n')
