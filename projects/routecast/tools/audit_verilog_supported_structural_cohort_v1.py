"""Full structural oracle across all supported non-fixture cases, no route labels."""
import json,sys,subprocess,ast
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];fp=R/'experiments/verilog_frontend_cohort_full_audit_v1_2026-10-10/verification.json';f=json.loads(fp.read_text());assert f['whole_cohort_complete'] and all(sha(k)==h for k,h in f['bindings'].items());base=R/'tools/audit_sha1_json_blif_structure_v1.py';body=base.read_text();D=R/'experiments/verilog_supported_structural_cohort_v1_2026-10-10';D.mkdir();A=D/'adapters';A.mkdir();fixture={'and_latch','multiclock_output_and_latch','multiclock_reader_writer','multiclock_separate_and_latch','single_ff','single_wire'};cases=[];bindings={str(Path(__file__)):sha(Path(__file__)),str(fp):sha(fp),str(base):sha(base)}
for row in f['rows']:
 name=row['name']
 if row['status']!='SUPPORTED_PRIMITIVES_ONLY' or name in fixture:continue
 reused={'sha':'sha1_json_blif_structure_v1_2026-10-10','blob_merge':'blob_merge_json_blif_structure_v1_2026-10-10'}.get(name)
 if reused:cases.append(dict(name=name,reused_proof=str(R/'experiments'/reused/'verification.json')));continue
 src=R/'experiments/verilog_frontend_cohort_v3_2026-10-10'/name;out=D/name
 code=body.replace("R=Path(__file__).resolve().parents[1]",f'R=Path({str(R)!r})').replace('experiments/sha1_frontend_readiness_v1_2026-10-10',str(src.relative_to(R))).replace('experiments/sha1_json_blif_structure_v1_2026-10-10',str(out.relative_to(R))).replace("dict(name='sha1',top='sha1')",f"dict(name={name!r},top={row['top']!r})")
 # Complete AST body identical modulo exact declared input/output/top bindings.
 normalized=code.replace(f'R=Path({str(R)!r})',"R=Path(__file__).resolve().parents[1]").replace(str(src.relative_to(R)),'experiments/sha1_frontend_readiness_v1_2026-10-10').replace(str(out.relative_to(R)),'experiments/sha1_json_blif_structure_v1_2026-10-10').replace(f"dict(name={name!r},top={row['top']!r})","dict(name='sha1',top='sha1')");assert ast.dump(ast.parse(normalized))==ast.dump(ast.parse(body))
 adapter=A/(name+'.py');adapter.write_text(code);bindings[str(adapter)]=sha(adapter);cases.append(dict(name=name,adapter=str(adapter),proof=str(out/'verification.json')))
assert len(cases)==8
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,scope='All8 primitive-supported non-fixture cohort cases,6 fresh full truth-table/pin/clock/init/top-port audits plus2 authenticated existing proofs. No source temporal/native/family admission, no cohort narrowed by proof ease; all failures retained.'),indent=2)+'\n');rows=[]
for case in cases:
 if 'reused_proof' in case:code=0;p=Path(case['reused_proof'])
 else:
  with (D/(case['name']+'.log')).open('w') as log:code=subprocess.run([sys.executable,case['adapter']],cwd=R,env={**__import__('os').environ,'PYTHONPATH':str(R/'tools')},stdout=log,stderr=subprocess.STDOUT).returncode
  p=Path(case['proof'])
 passed=False
 if p.exists():
  v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());passed=all(x['all_ports_truth_tables_pins_clocks_initial_states_exact'] for x in v['rows']);bindings[str(p)]=sha(p)
 rows.append(dict(name=case['name'],exit_code=code,proof=str(p),full_structure_pass=passed));(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print('STRUCTURAL_COHORT',case['name'],code,passed,flush=True)
assert all(sha(k)==h for k,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all8_attempted=len(rows)==8,all8_structural_pass=all(x['full_structure_pass'] for x in rows),functional_or_family_admitted=False),indent=2)+'\n')
