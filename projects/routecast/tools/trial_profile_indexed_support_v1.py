"""Actual indexed support extraction on every authenticated fresh-production UNSAT round."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
from cnf_rup_support_indexed_v1 import extract
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_direct_from_inputs_profile_v3_2026-10-09';D=E/'profile_indexed_support_v1_2026-10-09';D.mkdir(exist_ok=False);vp=E/'adder_direct_from_inputs_profile_verification_v3_2026-10-09/verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());rows=[];total=0
for iteration in range(94):
 p=B/f'round_{iteration}.json';record=json.loads(p.read_text());clauses=[record['encoding']['clauses'][i] for i in record['retained_indices']];start=time.perf_counter();core=extract(clauses,record['proof_result']);seconds=time.perf_counter()-start;total+=seconds;rows.append(dict(iteration=iteration,seconds=seconds,core=core,same_original_indices=core['original_indices']==record['core_clause_indices']));bindings[str(p)]=sha(p)
p=D/'cores.json';p.write_text(json.dumps(rows,indent=2)+'\n');bindings[str(p)]=sha(p);assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,rounds=len(rows),extract_seconds=total,same_support_count=sum(r['same_original_indices'] for r in rows),scope='Same archived94 real proof inputs; extraction timing only, no paired endtoend route speedup. Core differences may change live candidate-generation trajectory. Independent reduced RUP replay pending.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
