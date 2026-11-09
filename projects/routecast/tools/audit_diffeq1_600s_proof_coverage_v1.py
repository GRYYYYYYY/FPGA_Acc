"""All completed log obligations for exact full diffeq1 600s attempt."""
import json,re
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/diffeq1_archived_json_equivalence_600s_v1_2026-10-10';p=S/'receipt.json';v=json.loads(p.read_text());assert v['exit_code']==124 and not v['all_equiv_cells_proven_log'];assert all(sha(k)==h for k,h in v['bindings'].items());lp=S/'equivalence.log';text=lp.read_text();attempts=[]
for line in text.splitlines():
 m=re.match(r'^\s*Trying to prove \$equiv for (.+): (success!|failed\.)$',line)
 if m:attempts.append(dict(point=m[1],simple_proved=m[2]=='success!'))
assert len({x['point'] for x in attempts})==len(attempts)
failed_groups=Counter(re.sub(r' \[\d+\]$','',x['point']) for x in attempts if not x['simple_proved']);found=[int(x) for x in re.findall(r'Found (\d+) unproven \$equiv cells',text)];D=R/'experiments/diffeq1_600s_proof_coverage_v1_2026-10-10';assert not D.exists();D.mkdir();bindings={str(x):sha(x) for x in [Path(__file__).resolve(),p,lp]};out=dict(bindings=bindings,all_complete_logged_simple_attempts=attempts,found_obligation_counts=found,logged_unique_attempts=len(attempts),simple_success=sum(x['simple_proved'] for x in attempts),simple_failed=sum(not x['simple_proved'] for x in attempts),failed_groups=dict(failed_groups),induction_entered='Executing EQUIV_INDUCT' in text,scope='Complete terminal600s receipt/log authenticated, all complete logged points preserved; unfinished last line excluded. Failure means unproved, not counterexample. Source-to-archive temporal/initial/native/family admission false.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k not in ['bindings','all_complete_logged_simple_attempts','failed_groups']})
