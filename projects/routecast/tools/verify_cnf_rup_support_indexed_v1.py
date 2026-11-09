"""Exhaustive oracle and independent reduced proof replay for extracted support."""
import itertools,random,json
from pathlib import Path
from certified_cnf_dependency_cdcl_v1 import solve
from cnf_rup_support_indexed_v1 import extract
from verify_certified_cnf_dependency_cdcl_v1 import verify
from native_resume_prototype.source_binding_v2 import closure
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/cnf_rup_support_indexed_verification_v1_2026-10-09';D.mkdir(exist_ok=False);rng=random.Random(93742);tested=0
for case in range(80):
 clauses=[[rng.choice([-1,1])*rng.randint(1,6) for _ in range(rng.randint(1,3))] for _ in range(rng.randint(3,24))];result=solve(clauses,6)
 if result['status']!='UNSAT':continue
 core=extract(clauses,result);assert core['clauses']==[clauses[i] for i in core['original_indices']];assert not any(all(any(v[abs(x)-1]==(x>0) for x in c) for c in core['clauses']) for v in itertools.product([False,True],repeat=6));verify(core['clauses'],dict(status='UNSAT',model=None,rup_additions=core['rup_additions']));tested+=1
bindings=closure([Path(__file__)]);assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,unsat_cases=tested,scope='Original extracted subset exhaustively UNSAT and selected learned subsequence independently RUP checked. No minimum core or realinstance performance claim.'),indent=2)+'\n');print(tested)
