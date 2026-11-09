"""Fresh paired v8/v9 cold and branch-partial native behavioral parity."""
import json,os,re,shutil,subprocess,time,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from stream_native_route_audit_cached import audit
from native_resume_prototype.source_binding_v2 import closure
E=R/'experiments';D=E/'native_controlled_error_modes_v9_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter();prior=E/'mux32_old_placement_cold_control_2026-10-07';protocol=json.loads((prior/'protocol.json').read_text());assert all(sha(f)==h for f,h in protocol['inputs'].items());command=json.loads((prior/'receipt.json').read_text())['command'];source=R/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128';seed=E/'retained_branch_native_serialization_v1_2026-10-08/w32_m2.route';place=E/'mux_budget_move_cohort_2026-10-06/w32_m2/target.place';graph=Path(command[command.index('--read_rr_graph')+1]);bindings={**protocol['inputs'],**closure([Path(__file__)])}
for p in (prior/'protocol.json',prior/'receipt.json',seed,place,graph,Path(command[1]),seed.parent/'receipt.json'):bindings[str(p)]=sha(p)
seedreceipt=json.loads((seed.parent/'receipt.json').read_text());assert sha(seed)==next(x['route_sha256'] for x in seedreceipt['rows'] if x['width']==32 and x['index']==2)
rows=[]
for version,build in [('v8','native_resume_branch_partial_v8_2026-10-08'),('v9','native_resume_controlled_error_v9_2026-10-09')]:
 binary=R/'build'/build/'routecast_resume_vpr';br=binary.parent/'receipt.json';assert sha(binary)==json.loads(br.read_text())['binary_sha256']
 for p in (binary,br):bindings[str(p)]=sha(p)
 for mode in ('cold','partial'):
  assert all(sha(p)==h for p,h in bindings.items());w=D/f'{version}_{mode}';w.mkdir()
  for name in ('design.blif','design.net','design.place'):shutil.copyfile(source/name,w/name)
  shutil.copyfile(place,w/'design.place');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};cmd=[str(binary),*command[1:]]
  if mode=='partial':env.update(ROUTECAST_RESUME_SAME_PLACE_ROUTE=str(seed),ROUTECAST_RESUME_ALLOW_PARTIAL='1',ROUTECAST_RESUME_ALLOW_BRANCH_PARTIAL='1')
  (w/'command.json').write_text(json.dumps(dict(command=cmd,mode=mode,seed=str(seed) if mode=='partial' else None),indent=2)+'\n');t=time.perf_counter()
  with (w/'run.log').open('x') as log:code=subprocess.run(cmd,cwd=w,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
  text=(w/'run.log').read_text();assert code==0 and 'Completed routing consistency check successfully.' in text and 'VPR succeeded' in text;loaded='ROUTECAST_RESUME_LOADED_TREES' in text;assert loaded==(mode=='partial')
  proof=audit(graph,w/'output.route');assert proof['overflow_units']==0
  row=dict(version=version,mode=mode,exit_code=code,loaded=loaded,connections=len(proof['connections']),cpd_ns=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1],wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]),native_seconds=time.perf_counter()-t);rows.append(row)
  for p in w.iterdir():
   if p.is_file():bindings[str(p)]=sha(p)
  print(row,flush=True)
paths=lambda p:Counter((name,path) for name,ps in physical_paths(p).items() for path in ps)
for mode in ('cold','partial'):
 a=next(x for x in rows if x['version']=='v8' and x['mode']==mode);b=next(x for x in rows if x['version']=='v9' and x['mode']==mode);assert a['connections']==b['connections'] and a['cpd_ns']==b['cpd_ns'] and a['wirelength']==b['wirelength'];assert paths(D/f'v8_{mode}/output.route')==paths(D/f'v9_{mode}/output.route')
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,full_named_path_cpd_wire_parity_both_modes=True,component_seconds=time.perf_counter()-start,scope='Paired fresh native cold/branch-partial mux32 target-placement parity and original physical capacity audit. No canonical pin verification, independent model budget/STA target success, complete mode matrix, speedup or online transaction claim.'),indent=2)+'\n')
