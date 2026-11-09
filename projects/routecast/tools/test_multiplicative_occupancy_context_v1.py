"""Owner-set oracle verifies prices throughout release/commit transactions."""
import random,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from multiplicative_occupancy_context_v1 import Context
from source_binding_v2 import closure
class Search:
 def __init__(self,c,b):self.fields={'capacities':tuple(c)};self.base=tuple(b);self.closed=False
 def prepare(self,p,w,**kw):self.prices=dict(p);assert max(p.values())<=kw['price_ceiling']
 def patch_prices(self,p):self.prices.update(p)
rng=random.Random(20261011);checks=0
for trial in range(150):
 n=12;m=8;c=[rng.randrange(1,4) for _ in range(n)];b=[rng.randrange(1000) for _ in range(n)];span={i:rng.randrange(5) for i in range(n)};hist=[rng.randrange(6) for _ in range(n)];weight=7
 owners=[{j for j in range(m) if rng.randrange(3)==0} for _ in range(n)]
 s=Search(c,b);ctx=Context(s,c,b,m,span);ctx.start_round({i:hist[i]+span[i] for i in range(n)},weight,{i:len(x) for i,x in enumerate(owners)})
 for step in range(20):
  net=rng.randrange(m);old={i for i,x in enumerate(owners) if net in x};view=ctx.begin(old)
  for i in range(n):
   occ=len(owners[i]-{net});pres=1 if occ<c[i] else 2+occ-c[i];expected=b[i]*(1+hist[i])*pres+weight*span[i]-b[i]
   assert view.get(i)==s.prices[i]==expected;checks+=1
  new={i for i in range(n) if rng.randrange(3)==0}
  for i in old-new:owners[i].remove(net)
  for i in new-old:owners[i].add(net)
  ctx.finish({i:len(owners[i]) for i in old^new})
  try:view.get(0)
  except RuntimeError:pass
  else:raise AssertionError('stale snapshot usable')
  for i in range(n):
   occ=len(owners[i]);pres=1 if occ<c[i] else 2+occ-c[i]
   assert ctx.ledger.get(i,0)==occ and s.prices[i]==b[i]*(1+hist[i])*pres+weight*span[i]-b[i];checks+=1
out=R/'experiments/multiplicative_occupancy_contract_v1_2026-10-10';out.mkdir(exist_ok=False)
(out/'verification.json').write_text(json.dumps(dict(bindings=closure([Path(__file__)]),transactions=3000,node_checks=checks,owner_set_release_commit_price_and_stale_snapshot_pass=True,scope='Mock search transaction contract; no real graph/full feedback/native quality proof.'),indent=2)+'\n')
print('MULTIPLICATIVE TRANSACTIONS PASS',checks)
