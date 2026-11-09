"""Original prepared HDL vs actual frozen mapped JSON, combine local SAT and induction."""
import sys,json,time,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
src=R/'experiments/aes_family_candidate_v2_2026-10-08';r=json.loads((src/'receipt.json').read_text());p=json.loads((src/'protocol.json').read_text());assert all(sha(k)==v for k,v in r['bindings'].items());yosys=next(Path(k) for k in r['bindings'] if Path(k).name=='yosys');out=R/'experiments/aes_actual_json_equivalence_v3_2026-10-08';out.mkdir();bindings={**closure([Path(__file__)]),str(src/'receipt.json'):sha(src/'receipt.json'),str(yosys):sha(yosys)};rows=[]
for c in p['cases']:
 name=c['name'];top=c['top'];w=out/name;w.mkdir();hdl=src/name/'design.v';gate=src/name/'design.json';bindings.update({str(hdl):sha(hdl),str(gate):sha(gate)});script=f'read_verilog {hdl}\nhierarchy -check -top {top}\nproc\nflatten\nmemory\nopt\nopt_expr -undriven\nopt_clean\ncheck -assert\nrename {top} gold\ndesign -stash gold_store\nread_json {gate}\nhierarchy -check -top {top}\nrename {top} gate\ndesign -stash gate_store\ndesign -copy-from gold_store -as gold gold\ndesign -copy-from gate_store -as gate gate\nequiv_make gold gate equiv\nhierarchy -top equiv\nequiv_simple -undef\nequiv_induct -undef\nequiv_status -assert\n';(w/'check.ys').write_text(script);tick=time.perf_counter()
 with (w/'equivalence.log').open('w') as log:
  try:code=subprocess.run([str(yosys),'-s','check.ys'],cwd=w,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 rows.append({'name':name,'exit_code':code,'seconds':time.perf_counter()-tick,'files':{str(f):sha(f) for f in w.iterdir() if f.is_file()}});print(name,'ACTUAL JSON',code,flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'Actual frozen mapped JSON relation to prepared original HDL under Yosys unknown semantics. No extra synthesis target substituted, no native route/heldout evidence.'},indent=2)+'\n')
