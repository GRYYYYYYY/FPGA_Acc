"""All eight non-fixture supported cases: unchanged full temporal proof procedure."""
import ast,json,os,subprocess,sys
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
base=R/'tools/check_blob_merge_archived_json_equivalence_v1.py';body=base.read_text()
sp=R/'experiments/verilog_supported_structural_cohort_v1_2026-10-10/receipt.json';sr=json.loads(sp.read_text());assert sr['all8_attempted'] and all(sha(k)==v for k,v in sr['bindings'].items())
fp=R/'experiments/verilog_frontend_cohort_full_audit_v1_2026-10-10/verification.json';f=json.loads(fp.read_text());assert all(sha(k)==v for k,v in f['bindings'].items());tops={x['name']:x['top'] for x in f['rows']}
D=R/'experiments/supported_archived_json_equivalence_cohort_v1_2026-10-10';assert not D.exists();D.mkdir();A=D/'adapters';A.mkdir();cases=[];bindings={str(p):sha(p) for p in [Path(__file__).resolve(),base,sp,fp]}
for row in sr['rows']:
 name=row['name']
 if name in ('sha','blob_merge'):
  reuse=R/'experiments'/('sha1_archived_json_equivalence_v1_2026-10-10' if name=='sha' else 'blob_merge_archived_json_equivalence_v1_2026-10-10')/'receipt.json'
  if reuse.exists():cases.append(dict(name=name,reuse=str(reuse)));continue
 src='experiments/verilog_frontend_cohort_v3_2026-10-10/'+name;out=str((D/name).relative_to(R));top=tops[name]
 changes=[("R=Path(__file__).resolve().parents[1]",f'R=Path({str(R)!r})'),('experiments/blob_merge_frontend_readiness_v1_2026-10-10',src),('experiments/blob_merge_archived_json_equivalence_v1_2026-10-10',out),('RLE_BlobMerging',top)]
 code=body
 for old,new in changes:code=code.replace(old,new)
 normalized=code
 for old,new in reversed(changes):normalized=normalized.replace(new,old)
 assert ast.dump(ast.parse(normalized))==ast.dump(ast.parse(body))
 p=A/(name+'.py');p.write_text(code);bindings[str(p)]=sha(p);cases.append(dict(name=name,adapter=str(p),receipt=str(D/name/'receipt.json')))
assert len(cases)==8
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,scope='All8 retained including failed strict arm init oracle; unchanged original full source-to-archived-JSON equivalence commands and120s timeout. No source edits, no point exclusion. Weak induction and initial synchronization limitations remain; no native/family admission.'),indent=2)+'\n')
rows=[]
for c in cases:
 if 'reuse' in c:p=Path(c['reuse']);wrapper=None
 else:
  with (D/(c['name']+'.log')).open('w') as log:wrapper=subprocess.run([sys.executable,c['adapter']],cwd=R,env={**os.environ,'PYTHONPATH':str(R/'tools')},stdout=log,stderr=subprocess.STDOUT).returncode
  p=Path(c['receipt'])
 result=dict(name=c['name'],wrapper_exit=wrapper,receipt=str(p),receipt_present=p.exists())
 if p.exists():
  v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());bindings[str(p)]=sha(p);result.update(exit_code=v['exit_code'],all_equiv_cells_proven_log=v['all_equiv_cells_proven_log'],seconds=v['seconds'])
 rows.append(result);(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(result),flush=True)
assert all(sha(k)==h for k,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all8_attempted=len(rows)==8,native_or_family_admitted=False),indent=2)+'\n')
