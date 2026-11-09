"""Independent exhaustive Boolean truth oracle and RUP replay for signed batches."""
import json,random,itertools
from pathlib import Path
from certified_cnf_dependency_cdcl_pure_batch_v1 import solve
from verify_certified_cnf_dependency_cdcl_v1 import verify
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/certified_cnf_pure_batch_contract_v1_2026-10-19'
def main():
 D.mkdir(exist_ok=False);rng=random.Random(843013);fixtures=[[],[[]],[[1,2,3,4,5,6]],[[-1,-2,-3]],[[1,2],[-1,2],[1,-2],[-1,-2]]]
 for _ in range(200):fixtures.append([[rng.choice((-1,1))*rng.randint(1,6) for _ in range(rng.randint(1,4))] for _ in range(rng.randint(1,30))])
 counts={};batches=0;learned=0
 for clauses in fixtures:
  truth=any(all(any(values[abs(x)-1]==(x>0) for x in c) for c in clauses) for values in itertools.product((False,True),repeat=6));result=solve(clauses,6,max_nodes=1000);verify(clauses,result);assert result['status']==('SAT' if truth else 'UNSAT');counts[result['status']]=counts.get(result['status'],0)+1;batches+=result['pure_literal_batches'];learned+=len(result['rup_additions'])
 limited=solve([[1,2]],2,max_nodes=0);assert limited['status']=='UNKNOWN_SEARCH_LIMIT' and limited['visited_nodes']==1;verify([[1,2]],limited)
 files=[Path(__file__).resolve(),R/'tools/certified_cnf_dependency_cdcl_pure_batch_v1.py',R/'tools/verify_certified_cnf_dependency_cdcl_v1.py'];(D/'verification.json').write_text(json.dumps(dict(status='PURE_SIGNED_DECISION_BATCH_SOLVER_TRUTH_AND_RUP_CONTRACT_VERIFIED',bindings={str(p):sha(p) for p in files},cases=len(fixtures),status_counts=counts,pure_batches=batches,RUP_additions_replayed=learned,zero_work_bound_unknown_verified=True,scope='Pure literals are explicit signed decisions, not unproved root units. Same numeric propagation-round limit does not imply equal assignment work to the historical solver. SAT requires direct full original-clause model check and UNSAT requires independent RUP.'),indent=2)+'\n');print(dict(cases=len(fixtures),status_counts=counts,batches=batches,RUP_additions=learned),flush=True)
if __name__=='__main__':main()
