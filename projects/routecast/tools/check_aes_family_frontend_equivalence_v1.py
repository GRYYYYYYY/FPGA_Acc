"""Yosys temporal equivalence of frozen AES HDL preparation and LUT6 synthesis."""
import sys,json,time,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
src=R/'experiments/aes_family_candidate_v2_2026-10-08';p=json.loads((src/'protocol.json').read_text());receipt=json.loads((src/'receipt.json').read_text());assert receipt['protocol_sha256']==sha(src/'protocol.json') and all(sha(k)==v for k,v in p['bindings'].items());yosys=next(Path(k) for k in p['bindings'] if Path(k).name=='yosys');out=R/'experiments/aes_family_frontend_equivalence_v1_2026-10-08';out.mkdir();bindings={**closure([Path(__file__)]),str(src/'protocol.json'):sha(src/'protocol.json'),str(src/'receipt.json'):sha(src/'receipt.json'),str(yosys):sha(yosys)};rows=[]
for c in p['cases']:
 name=c['name'];w=out/name;w.mkdir();hdl=src/name/'design.v';bindings[str(hdl)]=sha(hdl);script=f"read_verilog {hdl}\nhierarchy -check -top {c['top']}\nproc\nflatten\nmemory\nopt\nequiv_opt -assert synth -top {c['top']} -flatten -lut 6\n";(w/'check.ys').write_text(script);tick=time.perf_counter()
 with (w/'equivalence.log').open('w') as log:
  try:code=subprocess.run([str(yosys),'-s','check.ys'],cwd=w,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 row={'name':name,'exit_code':code,'seconds':time.perf_counter()-tick,'files':{str(f):sha(f) for f in w.iterdir() if f.is_file()}};rows.append(row);print(name,'EQUIV',code,flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'Temporal induction candidate preparation vs synthesis only. Does not yet bind serialized BLIF re-import, VPR packing/place/RR/native route or prove unseen-family eligibility.'},indent=2)+'\n')
