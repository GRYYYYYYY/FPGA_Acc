"""Additional nonzero-ledger and partial-group publication oracle checks."""
import json,hashlib,random
from pathlib import Path
from collections import Counter
from atomic_multi_NET_group_session_v1 import Session
from verify_criticality_multi_NET_group_admission_v2_2026_10_18 import fixture

def main():
 rng=random.Random(48231);n=4;r=4;f,rc,slots,q,records=fixture(n,r,[2]*r,{(i,j):1 for i in range(n) for j in range(r)});choices=list(range(n));old=records(choices);ledger=Counter({i:1 for i in range(2*n)});ledger.update(2*n+j for j in choices);crit={i:dict(criticality_numerator=1,criticality_denominator=2) for i in range(n)};session=Session(f,rc,slots,q,old,ledger,crit,{i:0 for i in range(n)});committed=rejected=ledger_changed=partial_groups=0
 for _ in range(300):
  before=session.snapshot();nets=set(rng.sample(list(range(n)),rng.randrange(1,n+1)));proposal=choices.copy()
  for i in nets:proposal[i]=rng.randrange(r)
  full=records(proposal);candidate={i:full[i] for i in nets};newledger=Counter({i:1 for i in range(2*n)});newledger.update(2*n+j for j in proposal);delta=sum(max(0,newledger.get(i,0)-c)-max(0,before.ledger.get(i,0)-c) for i,c in enumerate(f['capacities']));epochs={i:before.epochs[i] for i in nets};ticket,answer=session.prepare(candidate,{},generation=before.generation,expected_epochs=epochs,price_epoch=before.price_epoch);assert answer['prospective_overflow_delta']==delta and answer['accepted']==(delta<=0)
  if ticket is None:assert session.snapshot() is before;rejected+=1;continue
  for i in nets:candidate[i][0]['answer']['physical_edge_ids'].clear() # Accepted private proposal must already be detached.
  session.commit(ticket,generation=before.generation,price_epoch=before.price_epoch);after=session.snapshot();assert dict(after.ledger)==dict(newledger);assert after.generation==before.generation+1 and before.generation+1==committed+1
  for i in range(n):assert after.epochs[i]==before.epochs[i]+(i in nets)
  expected=records(proposal)
  for i in range(n):assert tuple(after.records[i][0]['answer']['physical_edge_ids'])==tuple(expected[i][0]['answer']['physical_edge_ids'])
  ledger_changed+=dict(after.ledger)!=dict(before.ledger);partial_groups+=len(nets)<n;committed+=1;choices=proposal
 assert committed>0 and rejected>0 and ledger_changed>0 and partial_groups>0
 # Explicit last-owner removal and first-owner insertion, no zero-count ledger keys.
 f,rc,slots,q,records=fixture(2,3,[1,1,1],{(i,j):1 for i in range(2) for j in range(3)});initial=Counter({i:1 for i in range(6)});s=Session(f,rc,slots,q,records([0,1]),initial,{i:dict(criticality_numerator=1,criticality_denominator=2) for i in range(2)},{0:0,1:0});t,a=s.prepare(records([1,2]),{},generation=0,expected_epochs={0:0,1:0},price_epoch=0);assert a['accepted'];s.commit(t,generation=0,price_epoch=0);assert 4 not in s.snapshot().ledger and s.snapshot().ledger[5]==s.snapshot().ledger[6]==1
 root=Path(__file__).resolve().parents[1];p=root/'experiments/atomic_multi_NET_group_session_core_v1_2026-10-18/verification.json';prior=json.loads(p.read_text());assert all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==h for k,h in prior['bindings'].items());out=root/'experiments/atomic_multi_NET_group_session_updates_v2_2026-10-18';out.mkdir();files=[Path(__file__).resolve(),root/'tools/atomic_multi_NET_group_session_v1.py',p];result=dict(status='atomic_group_partial_scope_ledger_changes_and_detached_candidate_updates_pass',proposals=300,committed=committed,rejected=rejected,nonzero_ledger_change_commits=ledger_changed,partial_group_commits=partial_groups,last_owner_removal_and_first_owner_insertion_pass=True,accepted_candidates_detached_from_later_caller_mutation=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Small graph publication mechanics only; graph/RC copy and snapshot construction costs are not optimized or measured on real RR graphs. No real candidate search, forecast improvement or native/fullflow gain.');(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','scope']}))
if __name__=='__main__':main()
