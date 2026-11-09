"""Independent counted owner removal and frozen objective snapshot tests."""
from pathlib import Path
from collections import Counter
from types import MappingProxyType
import random,json,hashlib
from multi_NET_private_prices_v1 import sync,GroupPrices,groups
from cached_multiplicative_occupancy_context_v1 import Context
from verify_restart_present_context_v1_2026_10_18 import Search

def main():
 rng=random.Random(30811);checks=0
 for _ in range(100):
  caps=[rng.randrange(1,4) for _ in range(31)];base=[rng.randrange(1,1000) for _ in caps];spans={i:rng.randrange(1,6) for i in range(0,31,2)};hist={i:rng.randrange(5)+spans.get(i,0) for i in range(31)};ledger=Counter({i:rng.randrange(1,8) for i in range(31)});removed={i:rng.randrange(1,min(2,ledger[i])+1) for i in range(31)};search=Search(caps,base);ctx=Context(search,caps,base,20,spans);ctx.start_round(hist,19,ledger);view=GroupPrices(ctx,MappingProxyType(dict(ledger)),removed);shadow=Counter(ledger)
  for i,c in removed.items():shadow[i]-=c
  sync(ctx,shadow,set(removed));snapshot=ctx.begin(set())
  frozen={}
  for i in range(31):
   expected=base[i]*(1+hist[i]-spans.get(i,0))*(1+max(0,shadow[i]-caps[i]+1))+19*spans.get(i,0);assert snapshot.get(i)+base[i]==view.get(i)==expected;frozen[i]=view.get(i);checks+=1
  additions={i:shadow[i]+1 for i in range(31) if rng.randrange(2)};ctx.finish(additions)
  assert all(view.get(i)==frozen[i] for i in range(31));sync(ctx,ledger,set(range(31)));assert ctx.ledger==ledger
 # Independent deterministic pair oracle, inclusive shared source/resource ownership.
 owned={0:{0,4},1:{1,4},2:{2,4,5},3:{3,5}};ledger=Counter(n for ns in owned.values() for n in ns);caps=[1]*6;assert groups({0,2,3},owned,ledger,caps)==[(0,1),(2,3)]
 assert groups({3,2,0},owned,ledger,caps)==[(0,1),(2,3)]
 r=Path(__file__).resolve().parents[1];out=r/'experiments/multi_NET_private_price_contract_v1_2026-10-18';out.mkdir();files=[Path(__file__).resolve(),r/'tools/multi_NET_private_prices_v1.py'];(out/'verification.json').write_text(json.dumps(dict(status='counted_group_release_private_price_updates_and_frozen_common_scores_pass',independent_node_checks=checks,group_pairing_oracle_pass=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}),indent=2)+'\n');print('PRIVATE_GROUP_PRICES_PASS',checks)
if __name__=='__main__':main()
