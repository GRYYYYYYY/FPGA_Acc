"""Matched cold/seed route-stage continuation for all twenty coherent candidate bundles."""
import json,os,re,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];parent=root/'experiments/capacity_synchronized_reload_2026-10-06';proof=json.loads((parent/'verification.json').read_text());prior=json.loads((parent/'receipt.json').read_text());assert sha(parent/'receipt.json')==proof['receipt_sha256'];build=root/'build/native_search_seed_v3_2026-10-06';binary=build/'routecast_search_seed_vpr';br=json.loads((build/'receipt.json').read_text());assert sha(binary)==br['binary_sha256'];assert all(sha(p)==h for p,h in br['shared_inputs_sha256'].items());assert all(sha(p)==h for p,h in br['sources_sha256'].items());out=root/'experiments/capacity_native_seed_continuation_2026-10-06';out.mkdir();work=root/'work/capacity_native_seed_continuation_2026-10-06';work.mkdir();env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};results=[]
for row in prior['results']:
 assert row['status']=='RELOADED' and all(sha(p)==h for p,h in row['sha256'].items());index=row['pair_index'];source=Path(row['cwd'])/'reload'
 for mode in ('cold','seed'):
  cwd=work/f'{index}_{mode}';cwd.mkdir()
  for name in ('design.net','design.blif','design.place'):shutil.copyfile(source/name,cwd/name)
  shutil.copyfile(source/'design.route',cwd/'seed.route');inputs={str(p):sha(p) for p in cwd.iterdir()};cmd=row['reload_command'].copy();cmd[0]=str(binary);cmd[cmd.index('--analysis')]='--route';cmd[cmd.index('--route_file')+1]='output.route';runenv=dict(env)
  if mode=='seed':runenv['ROUTECAST_NATIVE_SEED']=str(cwd/'seed.route')
  start=time.perf_counter()
  with (cwd/'run.log').open('w') as log:code=subprocess.run(cmd,cwd=cwd,env=runenv,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
  text=(cwd/'run.log').read_text();cpd=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text);counts=re.findall(r'total_nets_routed:\s*(\d+)\s+total_connections_routed:\s*(\d+)\s+total_heap_pushes:\s*(\d+)\s+total_heap_pops:\s*(\d+)',text);result={'pair_index':index,'mode':mode,'exit_code':code,'native_success':code==0 and 'VPR succeeded' in text,'cpd_ns':float(cpd[1]) if cpd else None,'wall_s':time.perf_counter()-start,'search_counts':[list(map(int,c)) for c in counts],'input_cpd_ns':row['cpd_ns'],'command':cmd,'cwd':str(cwd),'inputs_sha256':inputs,'artifacts_sha256':{str(p):sha(p) for p in cwd.iterdir() if p.is_file()}};assert all(sha(p)==h for p,h in inputs.items());results.append(result);print(index,mode,code,result['cpd_ns'],result['search_counts'],flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'binary_sha256':sha(binary),'build_receipt_sha256':sha(build/'receipt.json'),'parent_verification_sha256':sha(parent/'verification.json'),'source_sha256':sha(Path(__file__)),'scope':'One cold and one seeded native route-stage process per frozen adder bundle, same packed netlist/place/private binary/options. Includes startup/import/routing, excludes predictor preparation and bundle creation; no statistically supported or whole-pipeline speed claim.'},indent=2)+'\n')
