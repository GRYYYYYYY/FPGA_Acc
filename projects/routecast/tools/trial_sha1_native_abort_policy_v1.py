"""Fixed diagnostic policy comparison, full100 budget, same archived width graph."""
import json,subprocess,os,shutil,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/sha1_native_width_cohort_v1_2026-10-10';rp=S/'receipt.json';r=json.loads(rp.read_text());assert r['all_cases_attempted'] and all(sha(k)==h for k,h in r['bindings'].items());p=json.loads((S/'protocol.json').read_text());D=R/'experiments/sha1_native_abort_policy_v1_2026-10-10';D.mkdir();bindings={str(Path(__file__)):sha(Path(__file__)),str(rp):sha(rp),str(S/'protocol.json'):sha(S/'protocol.json')};cases=[]
for width in [32,64,96]:
 row=next(x for x in r['rows'] if x['width']==width);assert all(sha(k)==h for k,h in row['files'].items());w=D/str(width);w.mkdir()
 for f in ['design.blif','design.net','design.place']:shutil.copyfile(S/str(width)/f,w/f);bindings[str(S/str(width)/f)]=sha(S/str(width)/f);bindings[str(w/f)]=sha(w/f)
 graph=S/str(width)/'rr_graph.xml';bindings[str(graph)]=sha(graph);cmd=next(x['command'] for x in p['cases'] if x['width']==width).copy();i=cmd.index('--write_rr_graph');del cmd[i:i+2];cmd+=['--read_rr_graph',str(graph),'--routing_failure_predictor','off','--router_init_wirelength_abort_threshold','1000000000']
 for path in [Path(cmd[0]),Path(cmd[1])]:bindings[str(path)]=sha(path)
 cases.append(dict(width=width,command=cmd))
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,timeout_per_case_seconds=300,scope='Exposed SHA policy diagnostic after prior outcomes. Frozen32/64/96 including successful control96, exact original width graph/placement/settings, predictor off, initial wirelength threshold1e9 (finite threshold, not proof disabled for all possible designs), max100. All outcomes once, no seed/model/threshold fit. Finite100-iteration failure is not mathematical infeasibility or strict heldout label. No uninstrumented full workflow gain.'),indent=2)+'\n');rows=[]
for case in cases:
 w=D/str(case['width']);tick=time.perf_counter()
 with (w/'native.log').open('w') as log:
  try:code=subprocess.run(case['command'],cwd=w,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=300).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 rows.append(dict(width=case['width'],exit_code=code,process_seconds=time.perf_counter()-tick,files={str(p):sha(p) for p in w.iterdir() if p.is_file()}));(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(case['width'],code,flush=True)
assert all(sha(k)==h for k,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_cases_attempted=len(rows)==3,classification_audit_pass=False),indent=2)+'\n')
