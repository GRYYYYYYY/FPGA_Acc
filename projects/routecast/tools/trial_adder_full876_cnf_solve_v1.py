"""Actual bounded solution of the frozen current component CNF."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from certified_cnf_dependency_cdcl_v1 import solve
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_full876_cnf_v1_2026-10-09';D=E/'adder_full876_cnf_solve_v1_2026-10-09';D.mkdir(exist_ok=False);vp=B/'verification.json';r=json.loads(vp.read_text());assert all(sha(p)==h for p,h in r['bindings'].items());bindings={**r['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};ep=B/'encoding.json';cnf=json.loads(ep.read_text());start=time.perf_counter();result=solve(cnf['clauses'],len(cnf['variables']),max_nodes=10000);seconds=time.perf_counter()-start;p=D/'result.json';p.write_text(json.dumps(result,indent=2)+'\n');bindings[str(p)]=sha(p);bindings[str(ep)]=sha(ep);assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,status=result['status'],visited_nodes=result['visited_nodes'],solve_seconds=seconds,scope='Bounded CNF solver output only; full clause proof/model and encoding require independent validation before route feasibility claims.'),indent=2)+'\n');print(dict(status=result['status'],visited_nodes=result['visited_nodes'],solve_seconds=seconds))
