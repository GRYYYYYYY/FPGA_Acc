import json,shutil,os,subprocess,re
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_scoped_sync_next_move_2026-10-06';work=root/'work/native_scoped_sync_next_move_2026-10-06';out.mkdir();work.mkdir();parent=root/'experiments/accepted_native_bundle_reload_2026-10-06';receipt=json.loads((parent/'receipt.json').read_text());verified=json.loads((parent/'verification.json').read_text());assert all(sha(p)==h for p,h in verified['sha256'].items());src=Path(receipt['cwd']);cmd=receipt['command'].copy();cmd[0]=str(root/'build/native_candidate_move_accept_scoped_2026-10-06/routecast_search_seed_vpr');cmd[cmd.index('--analysis')]='--route';cmd[cmd.index('--route_file')+1]='output.route';graph=cmd[cmd.index('--read_rr_graph')+1];results=[]
for name in ('resume','reject_next','accept_next'):
 cwd=work/name;cwd.mkdir();case=out/name;case.mkdir()
 for f in ('design.blif','design.net','design.place'):shutil.copyfile(src/f,cwd/f)
 shutil.copyfile(src/'design.route',cwd/'seed.route');env=os.environ.copy();env['ROUTECAST_NATIVE_SEED']=str(cwd/'seed.route');env.pop('ROUTECAST_TIMING_RESTORE_PROBE',None);env.pop('ROUTECAST_ACCEPT_CANDIDATE',None)
 if name!='resume':env['ROUTECAST_TIMING_RESTORE_PROBE']='1'
 if name=='accept_next':env['ROUTECAST_ACCEPT_CANDIDATE']='1'
 inputs={str(cwd/f):sha(cwd/f) for f in ('design.blif','design.net','design.place','seed.route')};(case/'command.json').write_text(json.dumps({'command':cmd,'cwd':str(cwd),'inputs_sha256':inputs},indent=2)+'\n')
 with (case/'run.log').open('w') as log:code=subprocess.run(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
 result={'case':name,'exit_code':code,'log_sha256':sha(case/'run.log')};assert all(sha(p)==h for p,h in inputs.items())
 if code==0:
  text=(case/'run.log').read_text();a=audit(graph,cwd/'output.route');assert len(a['connections'])==129 and a['overflow_units']==0;(case/'physical_audit.json').write_text(json.dumps(a,indent=2)+'\n');result.update(route_sha256=sha(cwd/'output.route'),packed_sha256=sha(cwd/'design.net.post_routing'),cpd_ns=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[1]));stats=re.search(r'total_nets_routed: (\d+) total_connections_routed: (\d+)',text);result.update(net_visits=int(stats[1]),connection_visits=int(stats[2]))
 results.append(result);print(name,code,flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'binary_sha256':sha(cmd[0]),'prior_bundle_verification_sha256':sha(parent/'verification.json'),'scope':'Next actual native route/move from postpacked accepted namespace in fresh process; fixed pair, not continuous in-memory move sequence or performance.'},indent=2)+'\n')
