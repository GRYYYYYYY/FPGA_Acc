import json,shutil,subprocess,os,re
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_seed_timing_modes_2026-10-06';work=root/'work/native_seed_timing_modes_2026-10-06';out.mkdir();work.mkdir();results=[]
for kind,parent in [('complete','native_search_seed_v3_2026-10-06'),('moved','native_move_seed_v5_2026-10-06')]:
 meta=json.loads((root/'experiments'/parent/'command.json').read_text());source=Path(meta['cwd']);graph=meta['command'][meta['command'].index('--read_rr_graph')+1]
 for mode in ('lookahead','all_critical'):
  name=kind+'_'+mode;cwd=work/name;cwd.mkdir();case=out/name;case.mkdir()
  for f in ('design.blif','design.net','design.place','seed.route'):shutil.copyfile(source/f,cwd/f)
  command=meta['command']+['--router_initial_timing',mode];env=os.environ.copy();env['ROUTECAST_NATIVE_SEED']=str(cwd/'seed.route')
  with (case/'run.log').open('w') as log:code=subprocess.run(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
  text=(case/'run.log').read_text();result={'case':name,'command':command,'exit_code':code,'log_sha256':sha(case/'run.log')}
  if code==0:
   a=audit(graph,cwd/'output.route');assert len(a['connections'])==129 and a['overflow_units']==0;(case/'physical_audit.json').write_text(json.dumps(a,indent=2)+'\n');result.update(cpd_ns=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[1]),route_sha256=sha(cwd/'output.route'))
  results.append(result);print(name,code,flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results},indent=2)+'\n')
