"""Cached occurrence solver on exact authenticated difficult recorded formula."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
from certified_cnf_dependency_cdcl_v2 import solve
from verify_certified_cnf_dependency_cdcl_v1 import verify
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'cached_occurrence_real_v1_2026-10-09';D.mkdir(exist_ok=False);p=E/'adder_direct_from_inputs_indexed_v4_2026-10-09/round_84.json';record=json.loads(p.read_text());bindings={str(p):sha(p),**closure([Path(__file__)])};cnf=record['encoding'];clauses=[cnf['clauses'][i] for i in record['retained_indices']];start=time.perf_counter();result=solve(clauses,len(cnf['variables']),10000);seconds=time.perf_counter()-start;rp=D/'result.json';rp.write_text(json.dumps(result,indent=2)+'\n');verify(clauses,result);same=result==record['proof_result'];bindings[str(rp)]=sha(rp);assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,status=result['status'],visited_nodes=result['visited_nodes'],same_full_model_proof_and_search_counters=same,solve_seconds=seconds,scope='Exact same real formula as original indexed freshround84; independent proof replay. Timing is unpaired standalone, not route workflow speedup.'),indent=2)+'\n');print(result['status'],result['visited_nodes'],seconds,same)
