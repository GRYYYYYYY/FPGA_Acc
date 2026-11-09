"""Exhaustive abstract transitions and randomized capacity-transaction properties."""
import json,itertools,random
from pathlib import Path
from collections import Counter
from monotone_package_transaction_v1 import rank,rollback_owners
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/monotone_package_transaction_contract_v1_2026-10-19'
def main():
 D.mkdir(exist_ok=False);normal=repairs=0
 for n in range(1,7):
  package=set(range(n))
  for labels in itertools.product(range(3),repeat=n):
   selected={i for i,x in enumerate(labels) if x};protected={i for i,x in enumerate(labels) if x==2};initial=rank(package,selected,protected);free=sorted(selected-protected)
   for target in package-selected:
    assert rank(package,selected|{target},protected)==initial-1;normal+=1
    for bits in range(1,1<<len(free)):
     removed={v for i,v in enumerate(free) if bits>>i&1};after=(selected-removed)|{target};newprotected=protected|{target};delta=rank(package,after,newprotected)-initial;assert delta==len(removed)-n-2<0 and protected<=newprotected<=after;repairs+=1
 rng=random.Random(731029);capacity_checks=0
 for _ in range(500):
  n=rng.randint(2,7);m=rng.randint(2,12);caps=[rng.randint(1,3) for _ in range(m)];outside=Counter({i:rng.randrange(c+1) for i,c in enumerate(caps)});usage=Counter();ownership={}
  for net in range(n):
   ns={i for i,c in enumerate(caps) if outside[i]+usage[i]<c and rng.randrange(3)==0};ownership[net]=ns;usage.update(ns)
  protected={net for net in ownership if rng.randrange(2)};fixed=Counter(i for net in protected for i in ownership[net]);candidate={i for i,c in enumerate(caps) if outside[i]+fixed[i]<c and rng.randrange(2)};removed=rollback_owners(caps,outside,ownership,protected,candidate)
  expected={net for net,ns in ownership.items() if net not in protected and any(i in candidate and outside[i]+usage[i]+1>caps[i] for i in ns)};assert set(removed)==expected and not set(removed)&protected;after=Counter(i for net,ns in ownership.items() if net not in removed for i in ns);after.update(candidate);assert all(outside[i]+after[i]<=caps[i] for i in range(m));capacity_checks+=1
 proof='For N package NETs, P protected and S selected, R=(N-|P|)(N+1)+(N-|S|)>=0. A normal insertion decreases R by1. A repair removes k unprotected selected NETs, inserts one previously absent NET, and protects it; deltaR=k-N-2<0 because k<=N-1. Protected trees never change. Each repair adds a distinct protected NET, so at most N-|P0| repairs. Every successful iteration strictly decreases nonnegative integer R; each iteration uses at most two complete searches. A failing core search terminates. At most2(R0+1) search calls, without an adjustable iteration quota. This proves termination and ledger safety, not routing completeness or efficiency.'
 (D/'proof.md').write_text(proof+'\n');bindings={str(p):sha(p) for p in (Path(__file__).resolve(),R/'tools/monotone_package_transaction_v1.py',D/'proof.md')};(D/'verification.json').write_text(json.dumps(dict(status='MONOTONE_PACKAGE_RANK_AND_CAPACITY_TRANSACTION_CONTRACT_VERIFIED',bindings=bindings,exhaustive_normal_transitions=normal,exhaustive_repair_transitions=repairs,random_capacity_transactions=capacity_checks,scope='Termination and transaction safety only; protected-core obstruction does not prove general infeasibility.'),indent=2)+'\n');print(dict(normal=normal,repairs=repairs,capacity_checks=capacity_checks),flush=True)
if __name__=='__main__':main()
