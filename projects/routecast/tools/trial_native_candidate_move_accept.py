import json,shutil,subprocess,os,re
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_candidate_move_accept_2026-10-06';work=root/'work/native_candidate_move_accept_2026-10-06';out.mkdir();work.mkdir();meta=json.loads((root/'experiments/predictor_native_trace_import_2026-10-06/command.json').read_text());source=Path(meta['cwd']);cmd=meta['command'].copy();cmd[0]=str(root/'build/native_candidate_move_accept_2026-10-06/routecast_search_seed_vpr');cmd[cmd.index('--analysis')]='--route';cmd[cmd.index('--route_file')+1]='output.route';graph=cmd[cmd.index('--read_rr_graph')+1];results=[]
for name in ('control','fault','accept'):
 cwd=work/name;cwd.mkdir();case=out/name;case.mkdir()
 for f in ('design.blif','design.net','design.place'):shutil.copyfile(source/f,cwd/f)
 shutil.copyfile(source/'design.route',cwd/'seed.route');env=os.environ.copy();env['ROUTECAST_NATIVE_SEED']=str(cwd/'seed.route');env.pop('ROUTECAST_TIMING_RESTORE_PROBE',None)
 if name!='control':env['ROUTECAST_TIMING_RESTORE_PROBE']='1'
 if name=='accept':env['ROUTECAST_ACCEPT_CANDIDATE']='1'
 with (case/'run.log').open('w') as log:code=subprocess.run(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
 result={'case':name,'exit_code':code,'log_sha256':sha(case/'run.log'),'command':cmd}
 if code==0:
  text=(case/'run.log').read_text();a=audit(graph,cwd/'output.route');assert len(a['connections'])==129 and a['overflow_units']==0;(case/'physical_audit.json').write_text(json.dumps(a,indent=2)+'\n');result.update(route_sha256=sha(cwd/'output.route'),cpd_ns=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[1]),packed_sha256=sha(cwd/'design.net.post_routing'))
 results.append(result);print(name,code,flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'scope':'Real packing sync plus synthetic delay mutation, restore full pb/lookup/maps and matrix then rebuild STA. Fixed layout, not whole move.'},indent=2)+'\n')
