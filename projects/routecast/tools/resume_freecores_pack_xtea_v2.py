import json,sys,subprocess,shutil,os,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
src=R/'experiments/freecores_candidate_pack_v1_2026-10-08';protocol=src/'protocol.json';p=json.loads(protocol.read_text());assert all(sha(k)==v for k,v in p['bindings'].items())
review=src/'failure_review.json';d=json.loads(review.read_text());assert d['xtea_native_not_started'] and all(sha(k)==v for k,v in d['bindings'].items()) and all(sha(k)==v for k,v in d['native_8051_files'].items())
case=next(x for x in p['cases'] if x['name']=='xtea');out=R/'experiments/freecores_candidate_pack_resume_v2_2026-10-08';out.mkdir();w=out/'xtea';w.mkdir();blif=src/'xtea/design.blif';shutil.copyfile(blif,w/'design.blif')
bindings={str(f):sha(f) for f in [Path(__file__),protocol,review,blif,w/'design.blif',Path(case['command'][0]),Path(case['command'][1])]}
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=case['command'],timeout_seconds=1200,scope='Resume only never-executed XTEA preregistered pack command after incorrect empty-place assertion; unchanged inputs/config. 8051 native returncode not persisted, log/artifacts retained separately.'),indent=2)+'\n');tick=time.perf_counter()
with (w/'pack.log').open('w') as log:
 try:code=subprocess.run(case['command'],cwd=w,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=1200).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
place=w/'design.place';placement_rows=[line for line in place.read_text().splitlines() if line.strip() and not line.startswith(('#','Netlist_File:','Array size:'))] if place.exists() else []
assert not placement_rows and not (w/'design.route').exists()
assert all(sha(k)==v for k,v in bindings.items())
(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,exit_code=code,seconds=time.perf_counter()-tick,files={str(f):sha(f) for f in w.iterdir() if f.is_file()},placement_data_rows=0,native_route_labels_generated=False,admitted_for_prediction=False),indent=2)+'\n');print('XTEA PACK',code,flush=True)
