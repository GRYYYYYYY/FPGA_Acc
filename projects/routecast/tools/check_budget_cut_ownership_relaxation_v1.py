"""Independent owner-function enumeration vs CNF and certified SAT/RUP solve."""
import json,random,itertools
from pathlib import Path
from budget_cut_ownership_relaxation_v1 import encode
from certified_cnf_dependency_cdcl_v2 import solve
from verify_certified_cnf_dependency_cdcl_v1 import verify
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/budget_cut_ownership_relaxation_contract_v1_2026-10-19'
def main():
 D.mkdir(exist_ok=False);rng=random.Random(513107);cases=assignments=0;counts={}
 fixtures=[[dict(NET=0,nodes=[0]),dict(NET=1,nodes=[0])],[dict(NET=0,nodes=[0,1]),dict(NET=1,nodes=[0,1])],[dict(NET=0,nodes=[0,1]),dict(NET=0,nodes=[1,2]),dict(NET=1,nodes=[0,2])]]
 for _ in range(120):
  n=rng.randint(1,4);m=rng.randint(1,5);fixtures.append([dict(NET=rng.randrange(n),nodes=rng.sample(range(m),rng.randint(1,m))) for _ in range(rng.randint(1,7))])
 for cuts in fixtures:
  encoding=encode(cuts);nodes=sorted({v for c in cuts for v in c['nodes']});eligible={n:sorted({c['NET'] for c in cuts if n in c['nodes']}) for n in nodes};truth=False
  for values in itertools.product(*([None]+eligible[n] for n in nodes)):
   owners=dict(zip(nodes,values));expected=all(any(owners[n]==c['NET'] for n in c['nodes']) for c in cuts);model={i:(owners[v['node']]==v['NET']) for i,v in enumerate(encoding['variables'],1)};actual=all(any(model[abs(lit)]==(lit>0) for lit in clause) for clause in encoding['clauses']);assert actual==expected;truth|=expected;assignments+=1
  result=solve(encoding['clauses'],len(encoding['variables']),max_nodes=1000);verify(encoding['clauses'],result);assert result['status']==('SAT' if truth else 'UNSAT');counts[result['status']]=counts.get(result['status'],0)+1;cases+=1
 bindings={str(p):sha(p) for p in (Path(__file__).resolve(),R/'tools/budget_cut_ownership_relaxation_v1.py',R/'tools/certified_cnf_dependency_cdcl_v2.py',R/'tools/verify_certified_cnf_dependency_cdcl_v1.py')};(D/'verification.json').write_text(json.dumps(dict(status='CUT_OWNERSHIP_RELAXATION_EQUALS_EXHAUSTIVE_OWNER_FUNCTIONS_WITH_CERTIFIED_SOLVES',bindings=bindings,cases=cases,owner_assignments=assignments,status_counts=counts,max_solver_nodes=1000,scope='Necessary ownership relaxation only, not original graph route feasibility or forecast quality.'),indent=2)+'\n');print(dict(cases=cases,owner_assignments=assignments,status_counts=counts),flush=True)
if __name__=='__main__':main()
