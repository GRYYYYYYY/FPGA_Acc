"""Temporal equivalence of actual archived mapped JSON vs actual serialized BLIF."""
import sys,json,time,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
src=R/'experiments/aes_family_candidate_v2_2026-10-08';p=json.loads((src/'protocol.json').read_text());r=json.loads((src/'receipt.json').read_text());assert r['protocol_sha256']==sha(src/'protocol.json') and all(sha(k)==v for k,v in r['bindings'].items());yosys=next(Path(k) for k in r['bindings'] if Path(k).name=='yosys');out=R/'experiments/aes_blif_roundtrip_v1_2026-10-08';out.mkdir();bindings={**closure([Path(__file__)]),str(src/'receipt.json'):sha(src/'receipt.json'),str(yosys):sha(yosys)};rows=[]
for c in p['cases']:
 name=c['name'];w=out/name;w.mkdir();j=src/name/'design.json';b=src/name/'design.blif';assert sha(j)==next(x for x in r['rows'] if x['name']==name)['files'][str(j)];assert sha(b)==next(x for x in r['rows'] if x['name']==name)['files'][str(b)];bindings.update({str(j):sha(j),str(b):sha(b)});top=c['top'];script=f'read_json {j}\nhierarchy -check -top {top}\nrename {top} gold\ndesign -stash gold_store\nread_blif {b}\nhierarchy -check -top {top}\nrename {top} gate\ndesign -stash gate_store\ndesign -copy-from gold_store -as gold gold\ndesign -copy-from gate_store -as gate gate\nequiv_make gold gate equiv\nhierarchy -top equiv\nequiv_induct -undef\nequiv_status -assert\n';(w/'check.ys').write_text(script);tick=time.perf_counter()
 with (w/'equivalence.log').open('w') as log:
  try:code=subprocess.run([str(yosys),'-s','check.ys'],cwd=w,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 row={'name':name,'exit_code':code,'seconds':time.perf_counter()-tick,'files':{str(f):sha(f) for f in w.iterdir() if f.is_file()}};rows.append(row);print(name,'BLIF',code,flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'Actual mapped JSON vs actual candidate BLIF temporal equality; original HDL relation separate, no VPR route or heldout claim.'},indent=2)+'\n')
