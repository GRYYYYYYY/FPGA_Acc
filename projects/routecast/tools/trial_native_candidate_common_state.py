import json,os,re,shutil,subprocess
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];prior=root/'experiments/native_candidate_retention_diverse_benchmark_2026-10-06';v=json.loads((prior/'verification.json').read_text());assert all(sha(p)==h for p,h in v['sha256'].items());pairs=json.loads((prior/'protocol.json').read_text())['pairs']['adder'];out=root/'experiments/native_candidate_common_state_2026-10-06';out.mkdir();work=root/'work/native_candidate_common_state_2026-10-06';work.mkdir();refs={}
for mode,d in [('cold','native_candidate_timing_gate_2026-10-06'),('retained','native_candidate_retained_search_2026-10-06')]:
 r=json.loads((root/'experiments'/d/'receipt.json').read_text());refs[mode]=next(x for x in r['results'] if x['design']=='adder')
(out/'protocol.json').write_text(json.dumps({'pairs':pairs,'source_sha256':refs['cold']['inputs_sha256'],'prior_protocol_sha256':sha(prior/'protocol.json'),'scope':'Previously frozen distinct adder pairs; each arm/pair restarts from identical original packed/place/route, no prefix accepts.'},indent=2)+'\n');rows=[]
source=root/'work/native_candidate_timing_gate_2026-10-06/adder'
for i,(a,b) in enumerate(pairs):
 for mode in ('cold','retained'):
  name=f'{i:02d}_{mode}';cwd=work/name;cwd.mkdir();case=out/name;case.mkdir();cmd=refs[mode]['command'];graph=cmd[cmd.index('--read_rr_graph')+1]
  for f in ('design.blif','design.net','design.place','seed.route'):shutil.copyfile(source/f,cwd/f)
  inputs={str(p):sha(p) for p in cwd.iterdir()};env=os.environ.copy();env.update(ROUTECAST_NATIVE_SEED=str(cwd/'seed.route'),ROUTECAST_TIMING_RESTORE_PROBE='1',ROUTECAST_MOVE_SEQUENCE='A',ROUTECAST_MOVE_PAIRS=f'{a} {b}')
  with (case/'run.log').open('w') as log:code=subprocess.run(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
  assert code==0 and all(sha(p)==h for p,h in inputs.items());log=(case/'run.log').read_text();before,candidate=map(float,re.search(r'before_cpd_ns=([0-9.]+) candidate_cpd_ns=([0-9.]+)',log).groups());accepted='accepted actual moved candidate after FULL check, packing sync and STA' in log
  for p in (cwd/'candidate_0.route',cwd/'output.route'):
   audited=audit(graph,p);assert len(audited['connections'])==516 and audited['overflow_units']==0;(case/(p.stem+'_audit.json')).write_text(json.dumps(audited,indent=2)+'\n')
  rows.append({'index':i,'pair':[a,b],'mode':mode,'exit_code':code,'before_cpd_ns':before,'candidate_cpd_ns':candidate,'accepted':accepted,'inputs_sha256':inputs,'log_sha256':sha(case/'run.log'),'candidate_sha256':sha(cwd/'candidate_0.route'),'final_route_sha256':sha(cwd/'output.route'),'packed_sha256':sha(cwd/'design.net.post_routing'),'binary_sha256':sha(cmd[0])});print(name,candidate,accepted,flush=True)
 comparisons=[]
 for j in range(i+1):
  c=next(x for x in rows if x['index']==j and x['mode']=='cold');r=next(x for x in rows if x['index']==j and x['mode']=='retained');assert c['before_cpd_ns']==r['before_cpd_ns'];comparisons.append({'index':j,'pair':c['pair'],'retained_minus_cold_cpd_ns':r['candidate_cpd_ns']-c['candidate_cpd_ns'],'decision_differs':r['accepted']!=c['accepted']})
 (out/'receipt.json').write_text(json.dumps({'results':rows,'comparisons':comparisons,'scope':'Candidate quality under identical starting native bundle and moved pair; process per candidate, no performance conclusion or prospective predictor claim.'},indent=2)+'\n')
