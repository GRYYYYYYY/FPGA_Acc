"""Exhaustive truth-table oracle and independent clause certificate replay."""
import json,itertools,random
from pathlib import Path
from certified_cnf_incremental_dpll_v2 import solve
from native_resume_prototype.source_binding_v2 import closure
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/certified_cnf_incremental_dpll_verification_v2_2026-10-09';D.mkdir(exist_ok=False)
def replay(node,assigned,clauses):
 assigned=dict(assigned)
 for lit in node['forced']:
  assert abs(lit) not in assigned
  residual=[]
  for clause in clauses:
   if any(abs(x) in assigned and assigned[abs(x)]==(x>0) for x in clause):continue
   residual.append([x for x in clause if abs(x) not in assigned])
  assert [lit] in residual;assigned[abs(lit)]=lit>0
 if node['kind']=='DEAD':assert all(abs(x) in assigned and assigned[abs(x)]!=(x>0) for x in clauses[node['clause']]);return
 assert node['kind']=='BRANCH';var=node['variable'];assert var not in assigned and [x['value'] for x in node['children']]==[True,False]
 for child in node['children']:replay(child['proof'],{**assigned,var:child['value']},clauses)
rng=random.Random(93742);counts={'SAT':0,'UNSAT':0}
for case in range(80):
 clauses=[[rng.choice([-1,1])*rng.randint(1,6) for _ in range(rng.randint(1,3))] for _ in range(rng.randint(3,24))];truth=any(all(any(values[abs(x)-1]==(x>0) for x in c) for c in clauses) for values in itertools.product([False,True],repeat=6));result=solve(clauses,6,10000);assert (result['status']=='SAT')==truth;counts[result['status']]+=1
 if truth:assert all(any(result['model'][abs(x)]==(x>0) for x in c) for c in clauses)
 else:replay(result['proof'],{},clauses)
bindings=closure([Path(__file__),R/'tools/certified_cnf_incremental_dpll_v2.py']);assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,cases=80,status_counts=counts,scope='All64 Boolean assignments per random6var case, SAT fullmodel clause check and UNSAT complete unit/branch/dead certificate replay.'),indent=2)+'\n');print(counts)
