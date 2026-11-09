"""Immutable snapshot of complete receipts and partial proof logs, never full-cohort pass."""
import json,re
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/supported_archived_json_equivalence_cohort_v2_2026-10-10';rp=S/'rows.json';raw=rp.read_bytes();rows=json.loads(raw);D=R/'experiments/supported_equivalence_progress_v2_2026-10-10';assert not D.exists();D.mkdir();(D/'observed_rows.json').write_bytes(raw);bindings={str(Path(__file__).resolve()):sha(Path(__file__)),str(D/'observed_rows.json'):sha(D/'observed_rows.json')};results=[]
for row in rows:
 p=Path(row['receipt']);
 if not p.exists():
  assert row['receipt_present'] is False and row['wrapper_exit']!=0;results.append(dict(name=row['name'],setup_failure=True,proof_receipt_present=False));continue
 v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());assert row['exit_code']==v['exit_code'] and row['all_equiv_cells_proven_log']==v['all_equiv_cells_proven_log'];log=p.parent/'equivalence.log';text=log.read_text();bindings[str(p)]=sha(p);bindings[str(log)]=sha(log);attempts=[]
 for line in text.splitlines():
  match=re.match(r'^\s*Trying to prove \$equiv for (.+): (success!|failed\.)$',line)
  if match:attempts.append(dict(point=match[1],simple_proved=match[2]=='success!'))
 found=[int(x) for x in re.findall(r'Found (\d+) unproven \$equiv cells',text)];unique=len({x['point'] for x in attempts});results.append(dict(name=row['name'],exit_code=v['exit_code'],equiv_make_entered='Executing EQUIV_MAKE' in text,simple_entered='Executing EQUIV_SIMPLE' in text,induct_entered='Executing EQUIV_INDUCT' in text,found_unproven_counts=found,complete_logged_simple_attempt_count=len(attempts),unique_points=unique,simple_success_count=sum(x['simple_proved'] for x in attempts),simple_failed_count=sum(not x['simple_proved'] for x in attempts),all_logged_simple_attempts=attempts,reported_all_proven=v['all_equiv_cells_proven_log']))
assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=results,whole8_cohort_complete=len(rows)==8,scope='Authenticated completed receipt prefix and every complete logged simple attempt; unfinished final log lines not proof. Timeout/failed simple means unproven, not counterexample. No full temporal/init/native/family admission.'),indent=2)+'\n');print(json.dumps([{k:v for k,v in x.items() if k!='all_logged_simple_attempts'} for x in results]))
