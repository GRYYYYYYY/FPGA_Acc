import json,subprocess,shutil,os,sys,re
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/aes_verbose_canonical_v1_2026-10-08';out.mkdir();exe=R/'build/native_verbose_sync_v2_2026-10-08/verbose_sync_vpr';bindings={str(exe):sha(exe),str(Path(__file__)):sha(Path(__file__))};rows=[]
for trial in ['aes_ignored_seed_admission_v1_2026-10-08','aes_cold_partition_audit_v1_2026-10-08']:
 for name in ['aes_cipher','aes_inv_cipher']:
  src=R/'experiments'/trial/(name+'_canonical');w=out/(trial+'_'+name);w.mkdir();receipt=json.loads((src.parent/'receipt.json').read_text());row=next(x for x in receipt['rows'] if x['name']==name);cmd=row['command'].copy();cmd[0]=str(exe);cmd[cmd.index('--route')]='--analysis';cmd[cmd.index('--route_file')+1]='design.route'
  for f in ['design.blif','design.net','design.place','design.route']:shutil.copyfile(src/f,w/f);bindings[str(src/f)]=sha(src/f)
  for f in [cmd[1],cmd[cmd.index('--read_rr_graph')+1]]:bindings[f]=sha(f)
  with (w/'reload.log').open('w') as log:code=subprocess.run(cmd,cwd=w,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
  text=(w/'reload.log').read_text();assert code==0 and 'VPR succeeded' in text;cpd=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[1]);assert cpd==row['cpd_ns'];m=int(re.search(r'Found (\d+) mismatches',text)[1]);f=int(re.search(r'Fixed (\d+) routing traces',text)[1]);rows.append({'trial':trial,'name':name,'command':cmd,'exit_code':code,'cpd_ns':cpd,'mismatches':m,'fixups':f,'files':{str(p):sha(p) for p in w.iterdir() if p.is_file()}});(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(trial,name,m,f,flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'Logging-only diagnostic original canonical reload; strict zero-fixup gate unchanged.'},indent=2)+'\n')
