"""Independent owner-set oracle, price-call counting and cached-hit invalidation."""
import random,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from cached_multiplicative_occupancy_context_v1 import Context
from source_binding_v2 import closure
from pre_route_endpoints import sha
class Search:
 def __init__(self,c,b):self.fields={'capacities':tuple(c)};self.base=tuple(b);self.closed=False
 def prepare(self,p,w,**kw):self.prices=dict(p);assert max(p.values())<=kw['price_ceiling']
 def patch_prices(self,p):self.prices.update(p)
class TracedContext(Context):
 calls=0
 def price(self,*args):self.calls+=1;return super().price(*args)
def rejects(fn,kind):
 try:fn()
 except kind:return
 raise AssertionError('invalid operation admitted')
rng=random.Random(20261013);checks=transactions=0
for trial in range(100):
 n=12;m=8;c=[rng.randrange(1,4) for _ in range(n)];b=[rng.randrange(1000) for _ in range(n)];span={i:rng.randrange(5) for i in range(n)}
 owners=[{j for j in range(m) if rng.randrange(3)==0} for _ in range(n)];s=Search(c,b);ctx=TracedContext(s,c,b,m,span);previous=None
 for round_ in range(3):
  hist=[rng.randrange(6) for _ in range(n)];weight=rng.randrange(8)
  ctx.start_round({i:hist[i]+span[i] for i in range(n)},weight,{i:len(x) for i,x in enumerate(owners)})
  for step in range(10):
   net=rng.randrange(m);old={i for i,x in enumerate(owners) if net in x};view=ctx.begin(old);before=ctx.calls
   if previous is not None:rejects(lambda:previous.get(0),RuntimeError)
   for repeat in range(3):
    for i in range(n):
     occ=len(owners[i]-{net});pres=1 if occ<c[i] else 2+occ-c[i];expected=b[i]*(1+hist[i])*pres+weight*span[i]-b[i]
     assert view.get(i)==s.prices[i]==expected;checks+=1
   assert ctx.calls-before==n
   for bad in [True,False,1.0,-1,n,'0']:rejects(lambda: view.get(bad),ValueError)
   s.closed=True;rejects(lambda:view.get(0),RuntimeError);s.closed=False
   rejects(lambda:ctx.begin(old),RuntimeError)
   new={i for i in range(n) if rng.randrange(3)==0}
   for i in old-new:owners[i].remove(net)
   for i in new-old:owners[i].add(net)
   ctx.finish({i:len(owners[i]) for i in old^new});rejects(lambda:view.get(0),RuntimeError);previous=view;transactions+=1
   for i in range(n):
    occ=len(owners[i]);pres=1 if occ<c[i] else 2+occ-c[i]
    assert ctx.ledger.get(i,0)==occ and s.prices[i]==b[i]*(1+hist[i])*pres+weight*span[i]-b[i]
# Zero is a cached value, not a miss sentinel.
s=Search([1],[0]);ctx=TracedContext(s,[1],[0],1,{0:0});ctx.start_round({0:0},0,{});v=ctx.begin(set());before=ctx.calls
assert v.get(0)==v.get(0)==0 and ctx.calls-before==1;ctx.finish();rejects(lambda:v.get(0),RuntimeError)
bindings=closure([Path(__file__)]);assert all(sha(p)==h for p,h in bindings.items())
out=Path(__file__).resolve().parents[1]/'experiments/cached_multiplicative_occupancy_contract_v1_2026-10-13';out.mkdir()
(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,transactions=transactions,node_queries=checks,all_owner_set_prices_and_cached_hit_guards_pass=True,price_computed_once_per_node_per_ticket=True,scope='Randomized transaction oracle with mock search price patches; full real model equivalence and timing separate.'),indent=2)+'\n')
print('PASS',transactions,'transactions',checks,'node queries, one price computation/node/ticket and stale cached-hit rejection')
