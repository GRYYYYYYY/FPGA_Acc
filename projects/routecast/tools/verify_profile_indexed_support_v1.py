"""Independent exact subset mapping and every reduced RUP certificate check."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
from verify_certified_cnf_dependency_cdcl_v1 import verify
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'profile_indexed_support_v1_2026-10-09';D=E/'profile_indexed_support_verification_v1_2026-10-09';D.mkdir(exist_ok=False);vp=B/'verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());rows=json.loads((B/'cores.json').read_text());assert len(rows)==94
for row in rows:
 p=E/f"adder_direct_from_inputs_profile_v3_2026-10-09/round_{row['iteration']}.json";record=json.loads(p.read_text());clauses=[record['encoding']['clauses'][i] for i in record['retained_indices']];core=row['core'];assert core['clauses']==[clauses[i] for i in core['original_indices']];assert core['rup_additions']==[record['proof_result']['rup_additions'][i] for i in core['addition_indices']];verify(core['clauses'],dict(status='UNSAT',model=None,rup_additions=core['rup_additions']))
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,status='ALL94_REDUCED_RUP_CERTIFICATES_PASS',extract_seconds=v['extract_seconds'],same_support_count=v['same_support_count'],scope='All94 real extracted original-clause subsets independently RUP certified UNSAT. Not minimum cores, no freshgeneration/native/performance conclusion.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
