"""Freeze all existing development cases before static-span feedback experiments."""
import sys,json,time,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha,extract
from source_binding_v2 import closure
runner=R/'tools/run_resident_soft_demand_wire_span_v1.py';out=R/'experiments/resident_wire_span_cohort_v1_2026-10-07';out.mkdir();names=['bigkey','dsip','misex3','frisc'];inputs={};endpoints={}
for name in names:
 epfile=R/f'experiments/mcnc_prospective_v1_2026-10-07/{name}/endpoints.json' if name!='frisc' else R/'experiments/frisc_endpoints_2026-10-05/endpoints.json';ep=json.loads(epfile.read_text());endpoints[name]=ep;inputs[str(epfile)]=sha(epfile);inputs.update({v['path']:v['sha256'] for v in ep['inputs'].values()})
bindings={**closure([Path(__file__),runner]),**inputs};assert all(sha(k)==v for k,v in bindings.items());(out/'protocol.json').write_text(json.dumps({'bindings':bindings,'order':names,'policy':'Existing development cohort NOT heldout. Unchanged initial exact RC floors and original max1ns/ceil1.5floor budgets; fixed two rounds and 50ps overuse price. Add static destination CHAN span price at 50ps/span from first feedback round; round0 includes all NETs owning CHAN. Round1 affected by new overuse only. Original simple single-parent whole NET transactions and budget-failure retention remain. No native labels and no tuning by results. Native quality/full-clock comparison must follow; no cost optimality within budgets claim.'},indent=2)+'\n');rows=[]
for name in names:
 begin=time.perf_counter();w=out/name;w.mkdir();ep=endpoints[name];fresh,mapping=extract(*(Path(ep['inputs'][k]['path']) for k in ['net','place','graph']));assert fresh['connections']==ep['connections'];epfile=w/'endpoints.json';epfile.write_text(json.dumps(fresh)+'\n');(w/'mapping.json').write_text(json.dumps(mapping)+'\n')
 with (w/'resident.log').open('w') as log:
  try:code=subprocess.run([sys.executable,str(runner),str(epfile),str(w/'resident')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 row={'name':name,'exit_code':code,'actual_conversion_estimator_seconds':time.perf_counter()-begin};rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,code,row['actual_conversion_estimator_seconds'],flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'files':{str(p):sha(p) for p in out.rglob('*') if p.is_file()}},indent=2)+'\n')
