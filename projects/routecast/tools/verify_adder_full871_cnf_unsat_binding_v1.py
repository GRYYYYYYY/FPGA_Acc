"""Join independently rebuilt real encoding with independently checked UNSAT proof."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_full871_cnf_unsat_binding_v1_2026-10-09';D.mkdir(exist_ok=False)
a=E/'adder_full871_cnf_structure_verification_v1_2026-10-09/verification.json';b=E/'adder_full871_cnf_solve_verification_v1_2026-10-09/verification.json';structure=json.loads(a.read_text());proof=json.loads(b.read_text());ep=E/'adder_full871_cnf_v1_2026-10-09/encoding.json'
assert structure['all_real_encoding_roles_and_clauses_rebuilt'] and proof['status']=='UNSAT' and proof['certificate_replay_pass']
assert structure['bindings'][str(ep)]==proof['bindings'][str(ep)]==sha(ep)
bindings=closure([Path(__file__)])
for p,r in ((a,structure),(b,proof)):
 for source,digest in r['bindings'].items():
  assert sha(source)==digest
  if source in bindings:assert bindings[source]==digest
  bindings[source]=digest
 bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,status='FIXED_FINITE_BANK_UNSAT',connections=516,scope='Authenticated full current871 candidate bank has no complete legal choice satisfying distinctNET capacities and sharedNET parent uniqueness. This does not prove full physical graph or arbitrary candidate banks infeasible.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
