"""Replay all authenticated cached-v5 UNSAT rounds with an independent indexed checker."""
import json, time
from pathlib import Path
from independent_indexed_rup_verify_v1 import verify
from native_resume_prototype.source_binding_v2 import closure
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments'
B=E/'adder_direct_from_inputs_cached_v5_2026-10-09'
D=E/'real_indexed_rup_check_v1_2026-10-09';D.mkdir(exist_ok=False)
vp=E/'adder_direct_from_inputs_cached_verification_v5_2026-10-09/verification.json'
v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])}
assert all(sha(p)==h for p,h in bindings.items())
rows=[];total=0;additions=0
for iteration in range(87):
    p=B/f'round_{iteration}.json';record=json.loads(p.read_text())
    clauses=[record['encoding']['clauses'][i] for i in record['retained_indices']]
    result=record['proof_result'];assert result['status']=='UNSAT'
    start=time.perf_counter();verify(clauses,result);seconds=time.perf_counter()-start
    total+=seconds;additions+=len(result['rup_additions'])
    rows.append(dict(iteration=iteration,seconds=seconds,additions=len(result['rup_additions']),status='PASS'))
    bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
out=dict(bindings=bindings,rows=rows,rounds=len(rows),rup_additions=additions,check_seconds=total,scope='Independent indexed full RUP replay of all87 authenticated UNSAT rounds. Archived inputs already checked by naive verifier. Diagnostic checker time only; not paired workflow gain, candidate generating trajectory or native quality evidence.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print({k:v for k,v in out.items() if k not in ('bindings','rows')})
