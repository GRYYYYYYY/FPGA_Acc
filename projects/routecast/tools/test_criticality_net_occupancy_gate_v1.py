"""Independent full-owner rebuild versus sparse transaction plan."""
import json,random
from collections import Counter
from pathlib import Path
from criticality_net_occupancy_gate_v1 import plan
from pre_route_endpoints import sha
rng=random.Random(389471);admitted=rejected=0
for trial in range(1200):
 n=rng.randrange(4,25);caps=[rng.randrange(1,4) for _ in range(n)]
 owners=[set(rng.sample(range(n),rng.randrange(1,n+1))) for _ in range(rng.randrange(2,10))]
 ledger=Counter(u for owner in owners for u in owner);idx=rng.randrange(len(owners));old=owners[idx];new=set(rng.sample(range(n),rng.randrange(1,n+1)))
 snapshot=ledger.copy();result=plan(caps,ledger,list(old)+list(old),list(new)+list(new));assert ledger==snapshot
 proposedowners=[new if i==idx else o for i,o in enumerate(owners)];expected=Counter(u for o in proposedowners for u in o)
 overflow=lambda counts:sum(max(0,counts.get(u,0)-caps[u]) for u in range(n))
 delta=overflow(expected)-overflow(ledger);assert result['prospective_overflow_delta']==delta
 if delta<=0:
  admitted+=1;applied=ledger.copy()
  for u,value in result['updates'].items():
   if value:applied[u]=value
   else:applied.pop(u,None)
  assert applied==expected and result['status']=='ADMIT_OCCUPANCY_REPLACEMENT'
 else:
  rejected+=1;assert result['status']=='RETAIN_OVERFLOW_INCREASE' and not result['updates'] and ledger==snapshot
# Another NET's owner prevents a falsely free old-node or net-count underflow.
for args in [([1,1],{},[0],[1]),([1,1],{0:1},[0],[2]),([1,0],{0:1},[0],[1]),([1,1],{0:1,1:-1},[0],[1])]:
 before=dict(args[1])
 try:plan(*args)
 except ValueError:pass
 else:raise AssertionError('invalid transaction admitted')
 assert args[1]==before
out=Path('experiments/criticality_net_occupancy_gate_contract_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve(),Path(__file__).with_name('criticality_net_occupancy_gate_v1.py').resolve()]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in files},transactions=1200,admitted=admitted,rejected=rejected,independent_full_owner_rebuild_pass=True,invalid_transaction_no_mutation_pass=4,scope='Pure occupancy plan only; no physical/full feedback/native claim.'),indent=2)+'\n');print('CRITICALITY OCCUPANCY GATE PASS',1200,admitted,rejected)
