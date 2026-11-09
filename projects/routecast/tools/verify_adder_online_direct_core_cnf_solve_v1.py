"""Independent complete clause model or unit/branch/dead proof replay."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_online_direct_core_cnf_solve_v1_2026-10-09';D=E/'adder_online_direct_core_cnf_solve_verification_v1_2026-10-09';D.mkdir(exist_ok=False);vp=B/'verification.json';report=json.loads(vp.read_text());bindings={**report['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());rp=B/'result.json';result=json.loads(rp.read_text());ep=E/'adder_online_direct_core_cnf_v1_2026-10-09/encoding.json';cnf=json.loads(ep.read_text());clauses=cnf['clauses'];visited=0
if result['status']=='SAT':
 model={int(v):b for v,b in result['model'].items()};assert set(model)==set(range(1,len(cnf['variables'])+1));assert all(any(model[abs(x)]==(x>0) for x in clause) for clause in clauses)
elif result['status']=='UNSAT':
 def walk(node,values):
  global visited
  visited+=1;values=dict(values)
  for lit in node['forced']:
   assert abs(lit) not in values
   assert any([x for x in clause if abs(x) not in values]==[lit] and not any(abs(x) in values and values[abs(x)]==(x>0) for x in clause) for clause in clauses)
   values[abs(lit)]=lit>0
  if node['kind']=='DEAD':assert all(abs(x) in values and values[abs(x)]!=(x>0) for x in clauses[node['clause']]);return
  assert node['kind']=='BRANCH';var=node['variable'];assert var not in values and [child['value'] for child in node['children']]==[True,False]
  for child in node['children']:walk(child['proof'],{**values,var:child['value']})
 walk(result['proof'],{});assert visited==result['visited_nodes']
else:assert result['status']=='UNKNOWN_SEARCH_LIMIT' and result['visited_nodes']==10001 and result['proof'] is None and result['model'] is None
for p in (rp,ep):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,status=result['status'],visited_nodes=result['visited_nodes'],certificate_replay_pass=result['status'] in ('SAT','UNSAT'),scope='Certificate of this exact CNF only. SAT requires path-choice physical/budget/capacity/parent/native gates; UNSAT requires independently validated real encoding before interpreting finite-bank infeasibility. Unknown proves neither.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
