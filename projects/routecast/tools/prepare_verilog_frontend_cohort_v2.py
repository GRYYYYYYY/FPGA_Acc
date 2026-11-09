"""Complete28-file frontend screening, not family or functional admission."""
import json,subprocess,sys
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];ip=R/'experiments/verilog_candidate_origin_inventory_v1_2026-10-10/inventory.json';inv=json.loads(ip.read_text());assert len(inv['rows'])==28 and all(sha(r['path'])==r['sha256'] for r in inv['rows'])
D=R/'experiments/verilog_frontend_cohort_v2_2026-10-10';D.mkdir();A=D/'adapters';A.mkdir();base=R/'tools/prepare_sha1_frontend_readiness_v1.py';text=base.read_text();bindings={str(Path(__file__)):sha(Path(__file__)),str(ip):sha(ip),str(base):sha(base)};plans=[]
# Top-level choices follow first source declaration; not outcome-driven. Multi-top ambiguity remains explicit.
for row in inv['rows']:
 name=Path(row['path']).stem;tops=row['declared_module_names'];assert tops
 reused={'sha':'experiments/sha1_frontend_readiness_v1_2026-10-10','blob_merge':'experiments/blob_merge_frontend_readiness_v1_2026-10-10'}.get(name)
 top={'arm_core':'arm_core'}.get(name,tops[0]);assert top in tops
 if reused:
  receipt=R/reused/'receipt.json';r=json.loads(receipt.read_text());assert all(sha(k)==h for k,h in r['bindings'].items());bindings[str(receipt)]=sha(receipt);plans.append(dict(name=name,source=row['path'],top='sha1' if name=='sha' else 'RLE_BlobMerging',reused_receipt=str(receipt),top_selection_needs_hierarchy_review=False));continue
 dest=D/name
 s=text.replace('experiments/sha1_frontend_readiness_v1_2026-10-10',str(dest.relative_to(R))).replace("source=S/'sha.v'",f"source=S/{Path(row['path']).name!r}").replace('sha1',top).replace("R=Path(__file__).resolve().parents[1]",f'R=Path({str(R)!r})').replace('Source-local SHA160','Source-local candidate').replace('SHA160','candidate').replace('cryptographic-domain','application-domain')
 adapter=A/(name+'.py');adapter.write_text(s);bindings[str(adapter)]=sha(adapter);bindings[row['path']]=row['sha256'];plans.append(dict(name=name,source=row['path'],top=top,adapter=str(adapter),top_selection_needs_hierarchy_review=len(tops)>1))
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,plans=plans,scope='All28 local candidate files,26 fresh plus2 authenticated existing receipts. Default first declared module except explicit arm_core arm_core; multi-module choices provisional and not native family admission. Same frozen synthesis/primitive rules/source unchanged/600s each; fixtures included but not representative research proof. No route labels, heldout or functional equivalence claim. Every unsupported/error/timeout retained; no retries or source repair.'),indent=2)+'\n');rows=[]
for plan in plans:
 if 'reused_receipt' in plan:rp=Path(plan['reused_receipt']);code=0
 else:
  with (D/(plan['name']+'.log')).open('w') as log:code=subprocess.run([sys.executable,plan['adapter']],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
  rp=D/plan['name']/'receipt.json'
 if rp.exists():
  r=json.loads(rp.read_text());assert all(sha(k)==h for k,h in r['bindings'].items());result={k:r.get(k) for k in ['exit_code','seconds','cell_types','unsupported_for_existing_boolean_schema']}
 else:result=dict(wrapper_exit_code=code,receipt_missing=True)
 rows.append(dict(name=plan['name'],top=plan['top'],receipt=str(rp),**result));(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print('FRONTEND',plan['name'],result.get('exit_code'),flush=True)
assert all(sha(k)==h for k,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all28_attempted=len(rows)==28,strict_family_admitted=False),indent=2)+'\n')
