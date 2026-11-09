"""Independent RUP replay and exhaustive six-variable oracle."""
import itertools,json,random
from pathlib import Path
from certified_cnf_dependency_cdcl_v1 import solve
from native_resume_prototype.source_binding_v2 import closure
from pre_route_endpoints import sha

def verify(clauses,result):
 database=[list(c) for c in clauses]
 for added in result['rup_additions']:
  assigned={};conflict=False
  for lit in added:
   if abs(lit) in assigned and assigned[abs(lit)]==(lit>0):conflict=True;break
   assigned[abs(lit)]=lit<0
  while not conflict:
   changed=False
   for clause in database:
    if any(abs(x) in assigned and assigned[abs(x)]==(x>0) for x in clause):continue
    remaining=set(x for x in clause if abs(x) not in assigned)
    if not remaining:conflict=True;break
    if len(remaining)==1:
     x=next(iter(remaining));assigned[abs(x)]=x>0;changed=True
   if not changed:break
  assert conflict,'non-RUP addition';database.append(added)
 if result['status']=='UNSAT':assert [] in result['rup_additions']
 if result['status']=='SAT':
  model={int(k):v for k,v in result['model'].items()};assert all(any(model[abs(x)]==(x>0) for x in c) for c in clauses)
 else:assert result['model'] is None

if __name__=='__main__':
 R=Path(__file__).resolve().parents[1];D=R/'experiments/certified_cnf_dependency_cdcl_verification_v1_2026-10-09';D.mkdir(exist_ok=False);rng=random.Random(93742);counts={};additions=0
 for case in range(80):
  clauses=[[rng.choice([-1,1])*rng.randint(1,6) for _ in range(rng.randint(1,3))] for _ in range(rng.randint(3,24))];truth=any(all(any(v[abs(x)-1]==(x>0) for x in c) for c in clauses) for v in itertools.product([False,True],repeat=6));result=solve(clauses,6);assert (result['status']=='SAT')==truth;verify(clauses,result);counts[result['status']]=counts.get(result['status'],0)+1;additions+=len(result['rup_additions'])
 bindings=closure([Path(__file__)]);assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,cases=80,status_counts=counts,rup_additions=additions),indent=2)+'\n');print(counts,additions)
