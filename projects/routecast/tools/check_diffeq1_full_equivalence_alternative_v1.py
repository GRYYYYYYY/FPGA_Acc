"""Full-point alternative SAT preparation, no selection or source projection."""
import ast,json,subprocess,sys,os
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];C=R/'experiments/supported_archived_json_equivalence_cohort_v2_2026-10-10';D=R/'experiments/diffeq1_full_equivalence_alternative_v1_2026-10-10';assert not D.exists();D.mkdir();cases=[];bindings={str(Path(__file__).resolve()):sha(Path(__file__))}
for name in ['diffeq1']:
 p=C/name/'receipt.json';v=json.loads(p.read_text());assert v['exit_code'] in [1,124] and not v['all_equiv_cells_proven_log'];assert all(sha(k)==h for k,h in v['bindings'].items());old=C/'adapters'/(name+'.py');body=old.read_text();original=str((C/name).relative_to(R));new=str((D/name).relative_to(R));changes=[(original,new),('timeout_s=120','timeout_s=600'),('timeout=120','timeout=600'),('equiv_simple -undef\\nequiv_induct','equiv_simple -undef -short -nogroup -seq 4\\nequiv_status\\nwrite_json pre_induction_equiv.json\\nequiv_induct')];code=body
 for a,b in changes:code=code.replace(a,b)
 normalized=code
 for a,b in changes:normalized=normalized.replace(b,a)
 assert ast.dump(ast.parse(normalized))==ast.dump(ast.parse(body));adapter=D/(name+'.py');adapter.write_text(code);bindings.update({str(x):sha(x) for x in [p,old,adapter]});cases.append(dict(name=name,adapter=str(adapter)))
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,scope='All points retained; original source/gate/init/undef same, full equiv_status assertion. Alternative simple SAT short cones/nogroup/max4 steps, pre-induction full state export,600s. Internal conditional cone/weak induction are not initialization proof or native/family admission.'),indent=2)+'\n');rows=[]
for case in cases:
 with (D/(case['name']+'.log')).open('w') as log:code=subprocess.run([sys.executable,case['adapter']],cwd=R,env={**os.environ,'PYTHONPATH':str(R/'tools')},stdout=log,stderr=subprocess.STDOUT).returncode
 p=D/case['name']/'receipt.json';row=dict(name=case['name'],wrapper_exit=code,receipt=str(p),receipt_present=p.exists())
 if p.exists():
  v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());bindings[str(p)]=sha(p);row.update(exit_code=v['exit_code'],all_equiv_cells_proven_log=v['all_equiv_cells_proven_log'])
 rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(row),flush=True)
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Alternative full-point proof attempts; no automatic admission.'),indent=2)+'\n')
