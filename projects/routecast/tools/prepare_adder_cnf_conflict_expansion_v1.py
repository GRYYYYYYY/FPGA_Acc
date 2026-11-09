"""Map certified negative PATH nogoods to original bank indices as search hints."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_cnf_conflict_expansion_v1_2026-10-09';D.mkdir(exist_ok=False)
vp=E/'adder_online_direct_core_cnf_unsat_binding_v1_2026-10-09/verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items())
ep=E/'adder_online_direct_core_cnf_v1_2026-10-09/encoding.json';rp=E/'adder_online_direct_core_cnf_dependency_cdcl_solve_v1_2026-10-09/result.json';dp=E/'adder_online_direct_core_joint_components_v1_2026-10-09/decomposition.json';cnf=json.loads(ep.read_text());result=json.loads(rp.read_text());domains=json.loads(dp.read_text())['domains'];cores=[];mapped=[]
for number,clause in enumerate(result['rup_additions']):
 paths=[]
 for lit in clause:
  role=cnf['variables'][abs(lit)-1];assert lit<0 and role['kind']=='PATH';cid,index=role['key'];paths.append([cid,domains[str(cid)][index]])
 mapped.append(dict(proof_addition=number,original_choices=paths))
 if len(paths)>1:
  for failed,index in paths:
   cores.append(dict(failed_connection=failed,selection={str(c):i for c,i in paths if c!=failed},proof_addition=number,certified_fixed_option=index))
p=D/'cores.json';p.write_text(json.dumps(dict(cores=cores,mapped_additions=mapped,scope='Certified fixed-bank nogoods mapped to search hints; not direct pairwise incompatibility or irreducible physical conflict cores.'),indent=2)+'\n');bindings[str(p)]=sha(p)
for p in (ep,rp,dp):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,hints=len(cores),status='CERTIFIED_NOGOOD_SEARCH_HINTS'),indent=2)+'\n');print(len(cores))
