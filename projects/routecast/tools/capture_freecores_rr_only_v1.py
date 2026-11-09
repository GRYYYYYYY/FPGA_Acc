import json,sys,subprocess,shutil,os,time,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha,extract
from source_binding_v2 import closure
src=R/'experiments/freecores_fixed_place_v1_2026-10-08';proof=src/'verification.json';v=json.loads(proof.read_text());assert v['both_complete_placements_pass'] and all(sha(k)==val for k,val in v['bindings'].items());rp=src/'receipt.json';r=json.loads(rp.read_text());assert all(sha(k)==val for k,val in r['bindings'].items()) and all(row['exit_code']==0 and all(sha(k)==val for k,val in row['files'].items()) for row in r['rows'])
prereg=R/'experiments/freecores_prospective_evaluation_prereg_v1_2026-10-08/protocol.json';pr=json.loads(prereg.read_text());assert all(sha(k)==val for k,val in pr['bindings'].items())
out=R/'experiments/freecores_rr_only_v1_2026-10-08';out.mkdir();bindings={**closure([Path(__file__)]),str(proof):sha(proof),str(rp):sha(rp),str(prereg):sha(prereg)};cases=[]
for case in json.loads((src/'protocol.json').read_text())['cases']:
 name=case['name'];w=out/name;w.mkdir()
 for file in ['design.blif','design.net','design.place']:shutil.copyfile(src/name/file,w/file);bindings[str(src/name/file)]=sha(src/name/file);bindings[str(w/file)]=sha(w/file)
 cmd=case['command'].copy();cmd[cmd.index('--place')]='--analysis';cmd.extend(['--route_file','missing.route','--write_rr_graph','rr_graph.xml','--check_route','full']);bindings.update({str(Path(cmd[i])):sha(Path(cmd[i])) for i in [0,1]});root=E.parse(w/'design.net').getroot();assert root.get('architecture_id')=='SHA256:'+sha(cmd[1]) and root.get('atom_netlist_id')=='SHA256:'+sha(w/'design.blif');cases.append(dict(name=name,command=cmd))
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,timeout_per_case_seconds=300,scope='Frozen pair fixed placement RR-only export then expected missing-route stop, no router/route labels. All complete packed endpoints with explicit root-clock exclusion, original native ignored flags still pending. Same unchanged experimental async architecture/model.'),indent=2)+'\n');rows=[]
for case in cases:
 w=out/case['name'];tick=time.perf_counter()
 with (w/'graph.log').open('w') as log:
  try:code=subprocess.run(case['command'],cwd=w,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=300).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 row=dict(name=case['name'],exit_code=code,status='REJECTED',native_graph_process_seconds=time.perf_counter()-tick)
 try:
  assert code==1 and (w/'rr_graph.xml').is_file() and not (w/'missing.route').exists() and not (w/'design.route').exists();text=(w/'graph.log').read_text();assert 'Message: Cannot open missing.route routing file' in text and 'Completed placement consistency check successfully.' in text
  ep,mapping=extract(w/'design.net',w/'design.place',w/'rr_graph.xml');(w/'endpoints.json').write_text(json.dumps(ep)+'\n');(w/'mapping.json').write_text(json.dumps(mapping)+'\n');row.update(status='GRAPH_AND_ENDPOINTS_CAPTURED',connections=len(ep['connections']),graph_sha256=ep['graph_sha256'])
 except Exception as error:row['error']=repr(error)
 row['files']={str(p):sha(p) for p in w.iterdir() if p.is_file()};rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(case['name'],row['status'],row.get('connections'),row.get('error'),flush=True)
assert all(sha(k)==v for k,v in bindings.items())
(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,native_route_labels_generated=False),indent=2)+'\n')
