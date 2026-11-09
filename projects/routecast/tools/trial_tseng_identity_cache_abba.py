"""Frozen ABBA import comparison with content-bound pin identities."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_identity_cache_abba_2026-10-06';out.mkdir();cache=out/'cache';source=(root/'tools/trial_tseng_joint_native_import.py').read_text();verifier=(root/'tools/verify_tseng_joint_native_import.py').read_text();runs=[]
for name,cached in [('warm',True),('a1',False),('b1',True),('b2',True),('a2',False)]:
 stem='tseng_identity_cache_'+name;tool='trial_'+stem+'.py';audit='verify_'+stem+'.py';s=source.replace('tseng_joint_native_import',stem)
 if cached:
  start=s.index("with (work/'identity.log').open('w')");end=s.index('nets={row',start)
  s=s[:start]+"from native_identity_cache import NativeIdentityCache\nimport time\nt=time.monotonic();cached_table,cache_info=NativeIdentityCache(Path("+repr(str(cache))+" )).get(icmd,work);cache_info['lookup_wall_s']=time.monotonic()-t;shutil.copyfile(cached_table,table);(work/'identity.log').write_text('Authenticated cached identity: '+json.dumps(cache_info)+'\\n');\n"+s[end:]
  s=s.replace("'scope':'Pre-route", "'identity_cache':cache_info,'scope':'Pre-route")
 (root/'tools'/tool).write_text(s);(root/'tools'/audit).write_text(verifier.replace('tseng_joint_native_import',stem));runs.append({'name':name,'cached':cached,'tool':tool,'audit':audit})
p={'order':runs,'sources_sha256':{n:sha(root/'tools'/n) for n in ['native_identity_cache.py',*[r[k] for r in runs for k in ('tool','audit')]]},'policy':'One measured cold cache population excluded from ABBA paired subtotal but retained separately; A native uncached probe, B authenticated cached probe; same frozen candidate/source/net/place/RR and nativeFULL/STA; no canonical or end-to-end speed claim.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');rows=[]
for run in runs:
 log=out/(run['name']+'.log');t=time.monotonic()
 with log.open('w') as stream:code=subprocess.run(['python3',str(root/'tools'/run['tool'])],cwd=root,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
 wall=time.monotonic()-t;assert code==0
 auditlog=out/(run['name']+'_audit.log');t=time.monotonic()
 with auditlog.open('w') as stream:acode=subprocess.run(['python3',str(root/'tools'/run['audit'])],cwd=root,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
 assert acode==0;rows.append({**run,'trial_wall_s':wall,'audit_wall_s':time.monotonic()-t,'log_sha256':sha(log),'audit_log_sha256':sha(auditlog)});print(run['name'],round(wall,3),flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'runs':rows},indent=2)+'\n')
