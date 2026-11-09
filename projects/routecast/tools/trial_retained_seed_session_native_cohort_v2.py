"""Actual branch-partial native resume for all12 fresh session seeds, serial."""
import json,os,re,shutil,subprocess,time,sys
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'));from source_binding_v2 import closure
D=R/'experiments/retained_seed_session_native_cohort_v2_2026-10-08';D.mkdir(exist_ok=False)
S=R/'experiments/retained_seed_session_cohort_v2_2026-10-08';proof=json.loads((S/'verification.json').read_text());assert proof['complete12_packed_sink_identity_and_serialized_bytes_equal'] and all(sha(p)==h for p,h in proof['bindings'].items())
seeds=json.loads((S/'receipt.json').read_text());pp=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json';cases=json.loads(pp.read_text())['cases']
prior=R/'experiments/mux32_old_placement_cold_control_2026-10-07';priorp=json.loads((prior/'protocol.json').read_text());assert all(sha(p)==h for p,h in priorp['inputs'].items());template=json.loads((prior/'receipt.json').read_text())['command']
build=R/'build/native_resume_branch_partial_v8_2026-10-08';binary=build/'routecast_resume_vpr';br=json.loads((build/'receipt.json').read_text());assert sha(binary)==br['binary_sha256']
bindings={**closure([Path(__file__)]),str(S/'verification.json'):sha(S/'verification.json'),str(S/'receipt.json'):sha(S/'receipt.json'),str(pp):sha(pp),str(binary):sha(binary),str(build/'receipt.json'):sha(build/'receipt.json'),str(Path(template[1])):sha(template[1])};plans=[]
for c in sorted(cases,key=lambda c:(c['width'],c['index'])):
 seed=next(x for x in seeds['rows'] if x['width']==c['width'] and x['index']==c['index']);target=json.loads(Path(c['target']).read_text());graph=Path(target['inputs']['graph']['path']);source=graph.parent;place=Path(target['inputs']['place']['path'])
 for p in (Path(seed['route']),Path(c['target']),Path(c['budget']),graph,source/'design.blif',source/'design.net',place):bindings[str(p)]=sha(p)
 assert bindings[str(source/'design.net')]==target['inputs']['net']['sha256']
 cmd=[str(binary),*template[1:]];cmd[cmd.index('--read_rr_graph')+1]=str(graph)
 plans.append(dict(width=c['width'],index=c['index'],seed=seed['route'],source=str(source),place=str(place),target=c['target'],budget=c['budget'],command=cmd))
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,plans=plans,scope='All12 fixed developer targets, actual v8 branchpartial loaded native route, seed1/workers1/FULL, no case omission or original budget changes. Provided seed component input; seed generation and independent audits outside this native component.'),indent=2)+'\n')
rows=[];start=time.perf_counter()
for plan in plans:
 tick=time.perf_counter();w=D/f'w{plan["width"]}_m{plan["index"]}';w.mkdir()
 for name in ('design.blif','design.net'):shutil.copyfile(Path(plan['source'])/name,w/name)
 shutil.copyfile(plan['place'],w/'design.place')
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_RESUME_SAME_PLACE_ROUTE=plan['seed'],ROUTECAST_RESUME_ALLOW_PARTIAL='1',ROUTECAST_RESUME_ALLOW_BRANCH_PARTIAL='1')
 with (w/'run.log').open('w') as log:code=subprocess.run(plan['command'],cwd=w,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
 text=(w/'run.log').read_text();cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text);wire=re.findall(r'Total wirelength:\s*(\d+)',text)
 row=dict(width=plan['width'],index=plan['index'],exit_code=code,elapsed_seconds=time.perf_counter()-tick,loaded_marker='ROUTECAST_RESUME_LOADED_TREES' in text,full_check='Completed routing consistency check successfully.' in text,vpr_succeeded='VPR succeeded' in text,cpd_ns=cpd[-1] if cpd else None,wirelength=int(wire[-1]) if wire else None,files={str(p):sha(p) for p in w.iterdir() if p.is_file()});rows.append(row)
 (D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(plan['width'],plan['index'],code,row['loaded_marker'],row['full_check'],flush=True)
elapsed=time.perf_counter()-start;assert len(rows)==12 and all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,protocol_sha256=sha(D/'protocol.json'),native_cohort_component_seconds=elapsed,scope='Actual native component, copying/setup/subprocess startup/close/log parse/archive output hashes included. Seed generation, initial protocol, final receipt and independent XML/Fraction/canonical audits outside; not complete original-input workflow.'),indent=2)+'\n');print('Native cohort terminal',elapsed)
