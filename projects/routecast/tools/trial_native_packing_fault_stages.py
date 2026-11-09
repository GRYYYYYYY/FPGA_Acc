import json,shutil,subprocess,os,re
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_packing_fault_stages_2026-10-06';work=root/'work/native_packing_fault_stages_2026-10-06';out.mkdir();work.mkdir();meta=json.loads((root/'experiments/predictor_native_trace_import_2026-10-06/command.json').read_text());src=Path(meta['cwd']);cmd=meta['command'];cmd[0]=str(root/'build/native_packing_fault_stages_2026-10-06/routecast_packing_rollback_vpr');results=[]
for stage in (1,2,3):
 for kind in ('runtime_error','bad_alloc'):
  name=f'{stage}_{kind}';cwd=work/name;cwd.mkdir();case=out/name;case.mkdir()
  for f in ('design.blif','design.net','design.place','design.route'):shutil.copyfile(src/f,cwd/f)
  env=os.environ.copy();env.update(ROUTECAST_PACKING_ROLLBACK_DIR=str(case),ROUTECAST_SYNC_FAULT_STAGE=str(stage),ROUTECAST_SYNC_FAULT_KIND=kind)
  with (case/'run.log').open('w') as log:code=subprocess.run(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
  text=(case/'run.log').read_text();assert code==0 and 'VPR succeeded' in text;assert f'sync fault reached stage={stage}' in text;assert sha(case/'before.txt')==sha(case/'restored.txt');cpd=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[1]);assert cpd==3.64796
  results.append({'stage':stage,'kind':kind,'exit_code':code,'cpd_ns':cpd,'state_sha256':sha(case/'before.txt'),'mutation_observed':sha(case/'before.txt')!=sha(case/'mutated.txt'),'log_sha256':sha(case/'run.log')});print(name,'pass',flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'binary_sha256':sha(cmd[0]),'command':cmd,'scope':'Injected runtime_error/bad_alloc type, not real memory exhaustion; packing rollback scope guard and active state equality, no whole move atomicity.'},indent=2)+'\n')
