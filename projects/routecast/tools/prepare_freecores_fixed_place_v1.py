import json,sys,shutil,subprocess,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
proof=R/'experiments/freecores_packed_signal_audit_v1_2026-10-08/admission_review.json';p=json.loads(proof.read_text());assert p['async_primitive_pin_structure_pass'] and all(sha(k)==v for k,v in p['bindings'].items())
structure=R/'experiments/freecores_json_blif_structure_v1_2026-10-08/verification.json';s=json.loads(structure.read_text());assert all(sha(k)==v for k,v in s['bindings'].items())
shared=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';vpr=shared/'build_tileplace_vpr/vpr/vpr';arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml'
out=R/'experiments/freecores_fixed_place_v1_2026-10-08';out.mkdir();bindings={**closure([Path(__file__),R/'tools/run_resident_soft_demand_affected_cache_v1.py']),str(proof):sha(proof),str(structure):sha(structure),str(vpr):sha(vpr),str(arch):sha(arch)};cases=[]
for name,src in [('8051',R/'experiments/freecores_candidate_pack_v1_2026-10-08/8051'),('xtea',R/'experiments/freecores_candidate_pack_resume_v2_2026-10-08/xtea')]:
 audit=R/'experiments/freecores_packed_signal_audit_v1_2026-10-08'/name/'async_signal_verification_v1.json';a=json.loads(audit.read_text());assert all(sha(k)==v for k,v in a['bindings'].items());bindings[str(audit)]=sha(audit)
 w=out/name;w.mkdir()
 for f in ['design.blif','design.net']:shutil.copyfile(src/f,w/f);bindings[str(src/f)]=sha(src/f);bindings[str(w/f)]=sha(w/f)
 cmd=[str(vpr),str(arch),'design.blif','--place','--net_file','design.net','--place_file','design.place','--route_chan_width','128','--num_workers','1','--seed','1'];cases.append(dict(name=name,command=cmd))
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,timeout_per_case_seconds=1200,route_chan_width=128,num_workers=1,seed=1,family_partition='Source project lineage: 8051 and XTEA evaluation candidates; AES siblings and Ethernet development. Domains processor/cryptography may overlap, not unseen domain proof. Global prior-use independence and original HDL relation still unproven.',frozen_model='Original simultaneous wholeNET resident affected-cache RC; initial exact RC, max1ns/ceil1.5floor, staticspan50ps plus dynamicoveruse50ps,2 rounds, no candidate-based retuning or label/case/round selection',scope='Fixed pair placement only before RR/endpoints/ignored-net partition/prediction. Same async experimental architecture. All failures/timeouts retained, no route labels. 8051 native pack code not persisted, authenticated success log/complete net/pin proof used as explicit artifact gate; not invented exit0.'),indent=2)+'\n');rows=[]
for case in cases:
 w=out/case['name'];tick=time.perf_counter()
 with (w/'place.log').open('w') as log:
  try:code=subprocess.run(case['command'],cwd=w,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=1200).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 assert not (w/'design.route').exists()
 row=dict(name=case['name'],exit_code=code,seconds=time.perf_counter()-tick,files={str(p):sha(p) for p in w.iterdir() if p.is_file()});rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print('PLACE',case['name'],code,flush=True)
assert all(sha(k)==v for k,v in bindings.items())
(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,native_route_labels_generated=False,scope='Native placement artifacts only, not original HDL/functional reset timing/strict heldout or prediction/netgain proof.'),indent=2)+'\n')
