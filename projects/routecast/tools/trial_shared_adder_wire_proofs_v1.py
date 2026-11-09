"""Seven full stage wire/atomic-coverage proofs with shared independent geometry."""
import json,runpy,time,shutil
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
import owned_wire_geometry_inventory_v1 as owned
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'shared_adder_wire_proofs_v1_2026-10-09';D.mkdir(exist_ok=False);indices=[6,9,12,15,19,22,25];bindings=closure([Path(__file__),R/'tools/owned_wire_geometry_inventory_v1.py']);scripts=[]
for stage,index in enumerate(indices,1):
 old=E/f'adder_shared_full_stage_{stage}_v3_2026-10-08';target=D/f'stage_{stage}';target.mkdir()
 for name in ['receipt.json','verification.json']+[f'step_{i}.json' for i in range(4)]:
  shutil.copyfile(old/name,target/name);assert sha(old/name)==sha(target/name)
  for p in (old/name,target/name):bindings[str(p)]=sha(p)
 source=R/f'tools/shared_full_step_{index}_v3.py';s=source.read_text();s=s.replace("D=E/'adder_shared_full_stage_"+str(stage)+"_v3_2026-10-08'",'D=R/'+repr(str(target.relative_to(R))))
 a=s.index('length={};before=sha(g)');b=s.index('assert sha(g)==before;rows=[]',a)
 s=s[:a]+"before=sha(g)\nfrom owned_wire_geometry_inventory_v1 import read\nlength=read(g,m['graph_sha256'])\n"+s[b:]
 script=R/f'tools/verify_shared_adder_wire_stage_{stage}_v1.py';assert not script.exists();script.write_text(s);scripts.append(script);bindings.update(closure([script]))
rows=[];start=time.perf_counter()
try:
 for stage,script in enumerate(scripts,1):
  runpy.run_path(str(script),run_name='__main__');owned.validate()
  a=json.loads((E/f'adder_shared_full_stage_{stage}_v3_2026-10-08/wire_verification.json').read_text());b=json.loads((D/f'stage_{stage}/wire_verification.json').read_text())
  assert a['rows']==b['rows'] and a['all4_wire_bounds_and_atomic_coverage_pass']==b['all4_wire_bounds_and_atomic_coverage_pass'];rows.append(dict(stage=stage,all4_full_proof_rows_equal=True))
 elapsed=time.perf_counter()-start;assert owned.builds==1 and owned.hits==6;negative=[]
 try:owned._length.__setitem__(0,999)
 except (TypeError,AttributeError):negative.append('geometry_mutation')
 else:raise AssertionError('mutation accepted')
 try:owned.read(owned._key[0],'0'*64)
 except ValueError:negative.append('wrong_epoch')
 else:raise AssertionError('epoch accepted')
finally:owned.clear()
assert all(sha(p)==h for p,h in bindings.items())
out=dict(bindings=bindings,rows=rows,component_seconds=elapsed,inventory_builds=1,hits=6,negative_checks=negative,scope='Seven full4-step wire/atomic coverage/unchanged outside/no new budgetfailure proofs; includes independent geometry coldparse and fresh perproof graph authentication. Input stage production/copies/finalreceipt excluded, no fullworkflow speedup.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(elapsed)
