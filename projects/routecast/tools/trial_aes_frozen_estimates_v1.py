"""Frozen mapped AES candidates, estimates produced before any native routing labels."""
import sys,json,time,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
src=R/'experiments/aes_rr_graph_only_v1_2026-10-08';vp=src/'verification.json';proof=json.loads(vp.read_text());assert all(r['pack_place_and_graph_only_inputs_pass'] for r in proof['rows']);assert proof['native_route_labels_created'] is False;out=R/'experiments/aes_frozen_estimates_v1_2026-10-08';out.mkdir();runner=R/'tools/run_resident_soft_demand_wire_span_v1.py';bindings={**closure([Path(__file__),runner]),str(vp):sha(vp)};names=['aes_cipher','aes_inv_cipher']
for name in names:
 epfile=src/name/'endpoints.json';ep=json.loads(epfile.read_text());bindings[str(epfile)]=sha(epfile);bindings.update({x['path']:x['sha256'] for x in ep['inputs'].values()});assert not any((src/name).glob('*.route'))
assert all(sha(k)==v for k,v in bindings.items());(out/'protocol.json').write_text(json.dumps({'bindings':bindings,'order':names,'policy':'Before any native routing labels, complete original nonclock queries. Unchanged fixed wire-span50ps two-round model, original exact floor/budget; both candidate siblings retained. No hyperparameter or case selection by outcomes. Frozen mapped BLIF/pack/place/RR are test inputs; original HDL semantic proof still unproven. Not a completed unseen-family gate or original AES functional proof. Future native metrics require independent physical audit.'},indent=2)+'\n');rows=[]
for name in names:
 w=out/name;w.mkdir();tick=time.perf_counter()
 with (w/'resident.log').open('w') as log:
  try:code=subprocess.run([sys.executable,str(runner),str(src/name/'endpoints.json'),str(w/'resident')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 row={'name':name,'exit_code':code,'estimator_process_wall_seconds':time.perf_counter()-tick,'files':{str(p):sha(p) for p in w.rglob('*') if p.is_file()}};rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,'ESTIMATE',code,flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'native_labels_used':False},indent=2)+'\n')
