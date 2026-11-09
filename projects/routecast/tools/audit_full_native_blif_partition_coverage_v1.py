"""Compose proof coverage from actual logs and exact partition definitions."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_native_blif_all_boundaries_v1_2026-10-09';pre=json.loads((P/'preflight.json').read_text());original=(P/'miter.v').read_text();defs=dict(re.findall(r'wire (\w+); assign \1 = ([^;]+);',original));pairs={b:(n,a) for b,n,a in pre['pairs']};ledger={};records=[]
paths=[E/'full_native_blif_boundary_pruned_partitions_v2_2026-10-09/partition_results.json',E/'full_native_blif_boundary_subpartitions_v3_2026-10-09/partition_results.json']
parents=[json.loads(p.read_text()) for p in paths];assert parents[1]['parent_results_sha256']==hashlib.sha256(paths[0].read_bytes()).hexdigest()
for index,(p,j) in enumerate(zip(paths,parents)):
 for r in j['results']:
  if index==0 and r['status']!='passed':continue
  v=p.parent/f'p{r["partition"]:02d}.v';text=v.read_text();assert hashlib.sha256(v.read_bytes()).hexdigest()==r['miter_sha256'];partdefs=dict(re.findall(r'wire (\w+); assign \1 = ([^;]+);',text));assert all(defs[k]==value for k,value in partdefs.items())
  expected=' | '.join(f'({pairs[b][0]} ^ {pairs[b][1]})' for b in r['targets']);assert re.search(r'assign bad = ([^\n]+);',text)[1]==expected
  log=R/r['log'];s=log.read_text()
  if r['status']=='passed':assert r['exit_code']==0 and 'SAT proof finished - no model found: SUCCESS!' in s
  assert r['status'] in ['passed','terminal_timeout']
  for b in r['targets']:assert b not in ledger;ledger[b]=r['status']
  records.append({'results':str(p.relative_to(R)),'partition':r['partition'],'status':r['status'],'targets':r['targets'],'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'exact_original_definitions':True})
assert set(ledger)==set(pairs)
out={'total_targets':len(ledger),'passed_targets':sum(s=='passed' for s in ledger.values()),'unresolved_targets':sorted(b for b,s in ledger.items() if s!='passed'),'records':records,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P/'preflight.json',P/'miter.v',*paths]},'scope':'Complete disjoint actual-log target coverage and exact original assignment preservation. Timeouts remain unresolved, regardless of absence of counterexamples; no Full, initialization or four-state admission.'}
D=E/'full_native_blif_partition_coverage_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'coverage_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'total_targets':out['total_targets'],'passed_targets':out['passed_targets'],'unresolved_targets':len(out['unresolved_targets'])},indent=2))
