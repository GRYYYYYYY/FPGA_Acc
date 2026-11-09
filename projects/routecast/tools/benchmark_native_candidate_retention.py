import json,os,shutil,subprocess,time,signal,statistics,re
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_candidate_retention_benchmark_2026-10-06';out.mkdir();work=root/'work/native_candidate_retention_benchmark_2026-10-06';work.mkdir();rows=[]
for design,count in [('multiplier',129),('adder',516)]:
 references={}
 for mode,d in [('cold','native_candidate_timing_gate_2026-10-06'),('retained','native_candidate_retained_search_2026-10-06')]:
  parent=root/'experiments'/d;v=json.loads((parent/'verification.json').read_text());assert all(sha(f)==h for f,h in v['sha256'].items());receipt=json.loads((parent/'receipt.json').read_text());references[mode]=next(x for x in receipt['results'] if x['design']==design)
 for repeat in range(6):
  for mode in (('cold','retained') if repeat%2==0 else ('retained','cold')):
   ref=references[mode];cmd=ref['command'];source=root/'work'/('native_candidate_timing_gate_2026-10-06' if mode=='cold' else 'native_candidate_retained_search_2026-10-06')/design;name=f'{design}_{repeat}_{mode}';cwd=work/name;cwd.mkdir();case=out/name;case.mkdir()
   for f in ('design.blif','design.net','design.place','seed.route'):shutil.copyfile(source/f,cwd/f)
   inputs={str(f):sha(f) for f in cwd.iterdir()};env=os.environ.copy();env.update(ROUTECAST_NATIVE_SEED=str(cwd/'seed.route'),ROUTECAST_TIMING_RESTORE_PROBE='1',ROUTECAST_MOVE_SEQUENCE='AAAA',ROUTECAST_MOVE_PAIRS='0 1 2 3 1 2 0 4')
   with (case/'run.log').open('w') as log:
    start=time.perf_counter();process=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
    def timeout_handler(*args):process.kill();process.wait();raise TimeoutError('candidate benchmark exceeded 60s')
    prior=signal.signal(signal.SIGALRM,timeout_handler);signal.alarm(60)
    try:code=process.wait()
    finally:signal.alarm(0);signal.signal(signal.SIGALRM,prior)
    elapsed=time.perf_counter()-start
   assert code==0 and all(sha(f)==h for f,h in inputs.items());assert sha(cwd/'output.route')==ref['route_sha256'] and sha(cwd/'design.net.post_routing')==ref['packed_sha256'];log=(case/'run.log').read_text();assert log.count('accepted actual moved candidate after FULL check, packing sync and STA')==2 and log.count('restored delay matrix and all edge-delay/STA metric observations')==2
   a=audit(cmd[cmd.index('--read_rr_graph')+1],cwd/'output.route');assert len(a['connections'])==count and a['overflow_units']==0
   rows.append({'design':design,'repeat':repeat,'mode':mode,'wall_s':elapsed,'exit_code':code,'inputs_sha256':inputs,'log_sha256':sha(case/'run.log'),'route_sha256':sha(cwd/'output.route'),'packed_sha256':sha(cwd/'design.net.post_routing'),'binary_sha256':sha(cmd[0])});print(name,round(elapsed,6),flush=True)
summary=[]
for design in ('multiplier','adder'):
 stats={}
 for mode in ('cold','retained'):
  values=[x['wall_s'] for x in rows if x['design']==design and x['mode']==mode];stats[mode]={'mean_s':statistics.mean(values),'median_s':statistics.median(values),'min_s':min(values),'max_s':max(values)}
 summary.append({'design':design,**stats,'retained_over_cold_mean_ratio':stats['retained']['mean_s']/stats['cold']['mean_s']})
(out/'receipt.json').write_text(json.dumps({'runs':rows,'summary':summary,'scope':'24 fresh native processes, alternating arm order, six repeats per arm/design; frozen existing route input and four timing-gated moves. Includes process/init/snapshot/copy/search/sync/export/restore; excludes seed production, RouteCast predictor/preparation and external audits. Shared host, no statistically general speed claim.'},indent=2)+'\n')
print(summary)
