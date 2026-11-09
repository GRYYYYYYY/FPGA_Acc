"""Full eight-stage audits sharing one independent authenticated XML parse."""
import json,runpy,time,shutil,tempfile
from pathlib import Path
from pre_route_endpoints import sha
import owned_independent_audit_inventory_v1 as owned
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'shared_independent_adder_audits_v1_2026-10-09';D.mkdir(exist_ok=False)
indices=[3,5,8,11,14,18,21,24];bindings=closure([Path(__file__),R/'tools/owned_independent_audit_inventory_v1.py']);rows=[]
for stage,index in enumerate(indices):
 old=E/f'adder_shared_full_stage_{stage}_v2_2026-10-08';target=D/f'stage_{stage}';target.mkdir()
 for name in ['receipt.json']+[f'step_{i}.json' for i in range(4)]:
  shutil.copyfile(old/name,target/name);assert sha(old/name)==sha(target/name);bindings[str(old/name)]=sha(old/name);bindings[str(target/name)]=sha(target/name)
 source=R/f'tools/shared_full_step_{index}_v2.py';text=source.read_text().replace('from unified_rr_audit_inventory_v2 import read','from owned_independent_audit_inventory_v1 import read').replace("D=E/'adder_shared_full_stage_"+str(stage)+"_v2_2026-10-08'",'D=R/'+repr(str(target.relative_to(R))))
 script=R/f'tools/verify_shared_independent_stage_{stage}_v1.py';assert not script.exists();script.write_text(text);bindings.update(closure([script]))
start=time.perf_counter()
try:
 for stage in range(8):
  tick=time.perf_counter();runpy.run_path(str(R/f'tools/verify_shared_independent_stage_{stage}_v1.py'),run_name='__main__');owned.validate();rows.append(dict(stage=stage,seconds=time.perf_counter()-tick,connections=2064))
 elapsed=time.perf_counter()-start;assert owned.builds==1 and owned.hits==7
 negative=[]
 for name,mutation in [('capacity',lambda:owned._inventory.physical.nodes.__setitem__(0,('SOURCE','999'))),('arc',lambda:owned._inventory.arc_multiplicities.__setitem__((0,0,0),1))]:
  try:mutation()
  except (TypeError,AttributeError):negative.append(name)
  else:raise AssertionError('inventory mutation accepted')
 try:owned.read(owned._key[0],'0'*64)
 except ValueError:negative.append('wrong_epoch')
 else:raise AssertionError('epoch accepted')
finally:owned.clear()
assert all(sha(p)==h for p,h in bindings.items())
out=dict(bindings=bindings,rows=rows,whole_audit_component_seconds=elapsed,inventory_builds=1,inventory_hits=7,negative_checks=negative,scope='Eight complete independent Fraction/physical/NETparent/capacity audits,16512 connections; graph freshly hashed before each reuse and after every audit. Provided stage outputs/copy preparation excluded; no whole workflow gain.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(elapsed)
