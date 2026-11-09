import json,shutil,subprocess,os,re,time
from pathlib import Path
from stream_native_route_audit import audit
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_seed_fanout_ablation_2026-10-06';out.mkdir();work=root/'work/native_seed_fanout_ablation_2026-10-06';work.mkdir();parent=root/'experiments/native_congested_seed_trace_2026-10-06';meta=json.loads((parent/'command.json').read_text());source=Path(meta['cwd']);cmd=meta['command'];graph=cmd[cmd.index('--read_rr_graph')+1];receipt=json.loads((parent/'receipt.json').read_text());assert sha(source/'seed.route')==receipt['seed_sha256'];results=[]
for name,options in [('default',[]),('partial',['--min_incremental_reroute_fanout','0'])]:
 cwd=work/name;cwd.mkdir();case=out/name;case.mkdir()
 for f in ('design.blif','design.net','design.place','seed.route'):shutil.copyfile(source/f,cwd/f)
 command=cmd+options;env=os.environ.copy();env['ROUTECAST_NATIVE_SEED']=str(cwd/'seed.route');(case/'command.json').write_text(json.dumps({'command':command,'cwd':str(cwd),'seed_sha256':sha(cwd/'seed.route')},indent=2)+'\n');start=time.monotonic()
 with (case/'run.log').open('w') as log:code=subprocess.run(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
 text=(case/'run.log').read_text();result={'case':name,'exit_code':code,'wall_s':time.monotonic()-start,'log_sha256':sha(case/'run.log')}
 if code==0:
  a=audit(graph,cwd/'output.route');assert len(a['connections'])==129 and a['overflow_units']==0;(case/'physical_audit.json').write_text(json.dumps(a,indent=2)+'\n');stats=re.search(r'total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',text);result.update(zip(['net_visits','connection_visits','heap_pushes','heap_pops'],map(int,stats.groups())));result.update(iterations=int(re.search(r'Successfully routed after (\d+)',text)[1]),cpd_ns=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[1]),output_sha256=sha(cwd/'output.route'),overflow_units=0,connections=129)
 results.append(result)
(out/'receipt.json').write_text(json.dumps({'results':results,'binary_sha256':sha(cmd[0]),'graph_sha256':sha(graph),'scope':'Same seed/input serial fanout policy ablation, normal first iteration retained, timing/native legality enabled. Single instrumented observations, no total-time speed proof.'},indent=2)+'\n');print(json.dumps(results,indent=2))
