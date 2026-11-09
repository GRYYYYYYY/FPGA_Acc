"""Fixed prospective pair, pack-only; immutable async architecture, no route labels."""
import json,sys,shutil,subprocess,os,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
src=R/'experiments/freecores_candidate_frontends_v1_2026-10-08';rp=src/'receipt.json';r=json.loads(rp.read_text());assert all(sha(k)==v for k,v in r['bindings'].items());assert all(sha(k)==v for row in r['rows'] for k,v in row['files'].items())
review=src/'admission_review.json';d=json.loads(review.read_text());assert all(sha(k)==v for k,v in d['bindings'].items());assert d['mips16_as_is_admission'] is False
shared=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';vpr=shared/'build_tileplace_vpr/vpr/vpr';arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml'
out=R/'experiments/freecores_candidate_pack_v1_2026-10-08';out.mkdir();bindings={str(p):sha(p) for p in [Path(__file__),rp,review,vpr,arch]};cases=[]
for name in ['8051','xtea']:
 row=next(x for x in r['rows'] if x['name']==name);assert row['exit_code']==0 and '$print' not in row['cell_types']
 w=out/name;w.mkdir();blif=src/name/'design.blif';shutil.copyfile(blif,w/'design.blif');bindings[str(blif)]=sha(blif);bindings[str(w/'design.blif')]=sha(w/'design.blif')
 cmd=[str(vpr),str(arch),'design.blif','--pack','--route_chan_width','128','--num_workers','1','--seed','1'];cases.append(dict(name=name,command=cmd))
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,timeout_per_case_seconds=1200,order='8051 then XTEA, no QoR selection',scope='Only pack compatibility diagnosis. Same async architecture as Ethernet, unchanged synthetic/uncharacterized reset timing. No route or placement labels generated; no original HDL equivalence, functional reset timing, heldout family or prediction admission. MIPS as-is undefined ROM excluded by frontend gate, not native QoR.'),indent=2)+'\n');rows=[]
for case in cases:
 w=out/case['name'];tick=time.perf_counter()
 with (w/'pack.log').open('w') as log:
  try:code=subprocess.run(case['command'],cwd=w,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=1200).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 assert not (w/'design.route').exists() and not (w/'design.place').exists()
 row=dict(name=case['name'],exit_code=code,seconds=time.perf_counter()-tick,files={str(p):sha(p) for p in w.iterdir() if p.is_file()});rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print('PACK',case['name'],code,row['seconds'],flush=True)
assert all(sha(k)==v for k,v in bindings.items())
(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,admitted_for_prediction=False,native_route_labels_generated=False,scope='All fixed pair pack outcomes retained; not original HDL equivalence, functional pin/reset/clock timing or heldout generalization gate.'),indent=2)+'\n')
