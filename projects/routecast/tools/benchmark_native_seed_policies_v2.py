"""Balanced same-input native stage benchmark; seed production explicitly excluded."""
import json,os,re,shutil,subprocess,time,statistics,itertools,signal
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_seed_policy_benchmark_v2_2026-10-06';out.mkdir();work=root/'work/native_seed_policy_benchmark_v2_2026-10-06';work.mkdir();source=root/'work/native_congested_seed_2026-10-06';command=json.loads((root/'experiments/native_congested_seed_2026-10-06/command.json').read_text())['command'];binary=root/'build/native_search_seed_v3_2026-10-06/routecast_search_seed_vpr';command[0]=str(binary);graph=command[command.index('--read_rr_graph')+1]
sequence=[policy for perm in itertools.permutations(('cold','whole','partial')) for policy in perm];inputs={str(p):sha(p) for p in [binary,Path(graph),*[source/n for n in ('design.blif','design.net','design.place','seed.route')]]};protocol={'sequence':sequence,'command_base':command,'inputs_sha256':inputs,'scope':'Uninstrumented native-stage wall incl process/import, frozen existing postroute seed. Excludes estimator/seed generation/serialization and external audit; not fullpipeline time.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results=[]
for index,policy in enumerate(sequence):
 cwd=work/f'{index:02d}_{policy}';cwd.mkdir();case=out/cwd.name;case.mkdir()
 for name in ('design.blif','design.net','design.place','seed.route'):shutil.copyfile(source/name,cwd/name)
 env=os.environ.copy();env.pop('ROUTECAST_NATIVE_SEED',None)
 if policy!='cold':env['ROUTECAST_NATIVE_SEED']=str(cwd/'seed.route')
 cmd=command+(['--min_incremental_reroute_fanout','0'] if policy=='partial' else []);(case/'command.json').write_text(json.dumps({'command':cmd,'cwd':str(cwd),'seed_enabled':policy!='cold'},indent=2)+'\n');start=time.monotonic()
 with (case/'run.log').open('w') as log:
  process=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
  def timeout_handler(signum,frame):
   process.kill();process.wait();raise TimeoutError('native benchmark exceeded 60 seconds')
  prior=signal.signal(signal.SIGALRM,timeout_handler);signal.alarm(60)
  try:code=process.wait()
  finally:signal.alarm(0);signal.signal(signal.SIGALRM,prior)
 wall=time.monotonic()-start;text=(case/'run.log').read_text();assert code==0 and 'VPR succeeded' in text and 'Completed routing consistency check successfully' in text
 physical=audit(graph,cwd/'output.route');assert len(physical['connections'])==129 and physical['overflow_units']==0;(case/'physical_audit.json').write_text(json.dumps(physical,indent=2)+'\n');stats=re.search(r'total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',text);result={'index':index,'policy':policy,'wall_s':wall,'cpd_ns':float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[1]),'iterations':int(re.search(r'Successfully routed after (\d+)',text)[1]),'route_sha256':sha(cwd/'output.route'),'log_sha256':sha(case/'run.log')};result.update(zip(['net_visits','connection_visits','heap_pushes','heap_pops'],map(int,stats.groups())));results.append(result);print(index,policy,round(wall,6),flush=True)
assert all(sha(p)==h for p,h in inputs.items());summary={}
for policy in ('cold','whole','partial'):
 rows=[r for r in results if r['policy']==policy];assert len({r['route_sha256'] for r in rows})==1;summary[policy]={'mean_s':statistics.mean(r['wall_s'] for r in rows),'median_s':statistics.median(r['wall_s'] for r in rows),'min_s':min(r['wall_s'] for r in rows),'max_s':max(r['wall_s'] for r in rows),'runs':len(rows),'cpd_ns':rows[0]['cpd_ns'],'connection_visits':rows[0]['connection_visits']}
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':results,'summary':summary,'inputs_unchanged':True,'all_18_routes_physical_129_overflow0':True,'scope':protocol['scope']},indent=2)+'\n');print(json.dumps(summary,indent=2))
