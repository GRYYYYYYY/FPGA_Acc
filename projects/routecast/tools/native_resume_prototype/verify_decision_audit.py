"""Verify complete ordered CBRR decisions and residual connection reason."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_decision_audit_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json') and all(sha(f)==h for f,h in p['bindings'].items())
rows=[]
for q in r['rows']:
 assert all(sha(f)==h for f,h in q['files'].items())
 calls=[int(x[1]) for x in q['events'] if x[0]=='RC_DECISION_CALL'];assert calls==list(range(1,len(calls)+1));groups=defaultdict(dict)
 for x in q['events']:
  if x[0]!='RC_DECISION':continue
  call,net,pin=int(x[1]),int(x[2]),int(x[4]);assert (net,pin) not in groups[call];groups[call][net,pin]=x
  reason=x[6];cur,bound,critical,threshold,tolerance=map(float,x[7:12])
  if reason=='zero':assert bound==0
  elif reason=='improved':assert cur<bound
  elif reason=='criticality':assert cur>=bound and critical<threshold
  elif reason=='delay':assert cur>=bound and critical>=threshold and cur<bound*tolerance
  else:assert reason=='selected' and cur>=bound and critical>=threshold and cur>=bound*tolerance
 assert all(len(g)==(936 if q['width']==16 else 1929) for g in groups.values())
 rows.append(dict(width=q['width'],mode=q['mode'],calls=len(calls),decisions=sum(len(g) for g in groups.values()),reasons=dict(Counter(x[6] for g in groups.values() for x in g.values()))))
q=r['rows'][0];target=[x for x in q['events'] if x[0]=='RC_DECISION' and x[3]=='d6_9' and x[4]=='1'];assert len(target)==11 and all(x[5]=='4018' and x[6]=='delay' and x[7]==x[8] and float(x[9])>=float(x[10]) for x in target)
dp=ROOT/'experiments/native_resume_residual_selection_w16_2026-10-07/diagnosis.json';d=json.loads(dp.read_text());assert all(sha(f)==h for f,h in d['bindings'].items());c=next(x for x in d['comparisons'] if x['path_owner']=='workflow' and x['net']=='d6_9');assert c['rr_sink']==4018 and c['modes']['workflow']['pin']==1
result=dict(rows=rows,residual_d6_9_pin1_reads=target,residual_mapping_sha256=sha(dp),residual_resume_minus_cold_last_inspection_ns=c['resume_minus_cold_ns'],receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),scope='All inspected connection decisions verified. Last working inspection may precede final routing; delay difference is not a complete final STA counterfactual. Criticality threshold is passed but achieved-delay bound rejects the residual connection throughout.')
(out/'decision_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(rows)
