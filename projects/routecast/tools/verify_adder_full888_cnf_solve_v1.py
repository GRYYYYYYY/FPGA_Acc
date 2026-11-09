"""Replay every learned clause against frozen actual CNF, including partial runs."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
from verify_certified_cnf_dependency_cdcl_v1 import verify
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_full888_cnf_solve_v1_2026-10-09';D=E/'adder_full888_cnf_solve_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
vp=B/'verification.json';report=json.loads(vp.read_text());bindings={**report['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items())
result=json.loads((B/'result.json').read_text());cnf=json.loads((E/'adder_full888_cnf_v1_2026-10-09/encoding.json').read_text());verify(cnf['clauses'],result)
if result['status']=='UNKNOWN_SEARCH_LIMIT':assert result['visited_nodes']==10001
if result['status']=='SAT':assert set(map(int,result['model']))==set(range(1,len(cnf['variables'])+1))
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,status=result['status'],visited_nodes=result['visited_nodes'],rup_additions_verified=len(result['rup_additions']),certificate_replay_pass=result['status'] in ('SAT','UNSAT'),scope='Every addition independently RUP checked. UNKNOWN has no feasibility conclusion; SAT requires physical route reconstruction; UNSAT applies only to this fixed finite bank encoding.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
