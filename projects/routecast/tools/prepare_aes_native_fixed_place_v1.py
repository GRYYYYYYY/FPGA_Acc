"""Fixed mapped AES candidates: independent pack/place only, no native route labels."""
import sys,json,shutil,subprocess,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
src=R/'experiments/aes_family_candidate_v2_2026-10-08';r=json.loads((src/'receipt.json').read_text());proof=R/'experiments/aes_json_blif_structure_v1_2026-10-08/verification.json';v=json.loads(proof.read_text());assert all(x['all_ports_truth_tables_pins_clocks_initial_states_exact'] for x in v['rows']);assert all(sha(k)==h for k,h in v['bindings'].items());shared=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';vpr=shared/'build_tileplace_vpr/vpr/vpr';arch=shared/'vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml';out=R/'experiments/aes_native_fixed_place_v1_2026-10-08';out.mkdir();bindings={**closure([Path(__file__)]),str(src/'receipt.json'):sha(src/'receipt.json'),str(proof):sha(proof),str(vpr):sha(vpr),str(arch):sha(arch)};cases=[]
for item in r['rows']:
 name=item['name'];blif=src/name/'design.blif';assert sha(blif)==item['files'][str(blif)];bindings[str(blif)]=sha(blif);w=out/name;w.mkdir();shutil.copyfile(blif,w/'design.blif');cmd=[str(vpr),str(arch),'design.blif','--pack','--place','--net_file','design.net','--place_file','design.place','--route_chan_width','128','--num_workers','1','--seed','1'];cases.append({'name':name,'command':cmd})
(out/'protocol.json').write_text(json.dumps({'bindings':bindings,'cases':cases,'timeout_per_case_s':300,'scope':'Both frozen mapped siblings pack/place only, NOT native routing labels or heldout outcome. Existing mappedJSON/BLIF structure audited; originalHDL semantic proof remains separate/pending and not claimed. Fixed width128/seed1/worker1/default place settings; all outcomes retained, no native QoR-selected case or parameter changes.'},indent=2)+'\n');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};rows=[]
for c in cases:
 name=c['name'];w=out/name;tick=time.perf_counter()
 with (w/'pack_place.log').open('w') as log:
  try:code=subprocess.run(c['command'],cwd=w,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 rows.append({'name':name,'exit_code':code,'seconds':time.perf_counter()-tick,'files':{str(f):sha(f) for f in w.iterdir() if f.is_file()}});(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,'PACK PLACE',code,flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'bindings':bindings,'rows':rows},indent=2)+'\n')
