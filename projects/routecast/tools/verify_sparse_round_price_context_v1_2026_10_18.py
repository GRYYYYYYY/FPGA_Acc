"""Deterministic differential lifecycle validation, not performance evidence."""
import sys,json,random,hashlib
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent))
from cached_multiplicative_occupancy_context_v1 import Context as Dense
from sparse_round_price_context_v1 import Context as Sparse
from native_price_buffer_store_v1 import Store

def main():
 r=random.Random(20261018);n=257
 caps=tuple(r.randrange(1,5) for _ in range(n));base=tuple(r.randrange(1,1000) for _ in range(n));spans={i:r.randrange(50) for i in range(n)}
 owners=[set(r.sample(range(n),15)) for _ in range(20)]
 ledger=Counter(x for owned in owners for x in owned);encoded=Counter(spans)
 stores=[Store({'capacities':caps},base) for _ in range(2)]
 a=Dense(stores[0],caps,base,20,spans);b=Sparse(stores[1],caps,base,20,spans,epoch='fixed-input-v1')
 for c in (a,b):c.start_round(encoded,3,ledger)
 buffer=b.search.backends[1].forward.price
 checks=0;rejections=0
 def same():
  nonlocal checks
  assert a.search.prices==b.search.prices
  assert a.ledger==b.ledger
  assert all(b.search.backends[1].forward.price[i]==v for i,v in enumerate(b.search.prices))
  assert b.search.backends[1].forward.price is buffer
  checks+=1
 def reject(fn):
  nonlocal rejections
  before=(list(b.history),list(b.search.prices),dict(b.ledger),b.max_history,b.search.price_ceiling)
  try:fn()
  except (ValueError,RuntimeError):pass
  else:raise AssertionError('invalid input admitted')
  assert before==(list(b.history),list(b.search.prices),dict(b.ledger),b.max_history,b.search.price_ceiling)
  rejections+=1
 same()
 for round_id in range(100):
  increments={i:r.randrange(1,4) for i in r.sample(range(n),7)}
  reject(lambda:b.advance_round(increments,3,ledger,epoch='stale'))
  reject(lambda:b.advance_round({n:1},3,ledger,epoch=b.epoch))
  reject(lambda:b.advance_round({0:-1},3,ledger,epoch=b.epoch))
  reject(lambda:b.advance_round({0:True},3,ledger,epoch=b.epoch))
  reject(lambda:b.advance_round({0:2**128},3,ledger,epoch=b.epoch))
  reject(lambda:b.advance_round({},4,ledger,epoch=b.epoch))
  drift=Counter(ledger);drift[0]=(drift[0]+1)%20
  reject(lambda:b.advance_round({},3,drift,epoch=b.epoch))
  encoded.update(increments)
  a.start_round(encoded,3,ledger);b.advance_round(increments,3,ledger,epoch=b.epoch);same()
  for k in range(10):
   oid=r.randrange(len(owners));old=owners[oid];new=set(r.sample(range(n),15))
   views=[c.begin(old) for c in (a,b)]
   assert [views[0].get(i) for i in range(n)]==[views[1].get(i) for i in range(n)]
   same();reject(lambda:b.advance_round({},3,ledger,epoch=b.epoch))
   if k%3==0:
    for c in (a,b):c.finish()
   else:
    updated=Counter(ledger);updated.subtract(old);updated.update(new)
    updates={i:updated[i] for i in old|new}
    for c in (a,b):c.finish(updates)
    ledger=+updated;owners[oid]=new
   for view in views:
    try:view.get(0)
    except RuntimeError:pass
    else:raise AssertionError('stale view admitted')
   same()
 b.search.close();reject(lambda:b.advance_round({},3,ledger,epoch=b.epoch))
 return {'status':'pass','rounds':100,'transactions':1000,'complete_state_comparisons':checks,'invalid_round_rejections_without_mutation':rejections,'retained_same_wide_price_buffer':True,'seed':20261018,'real_mmc_trajectory_validated':False,'performance_claim':False,'source_sha256':hashlib.sha256(Path(__file__).with_name('sparse_round_price_context_v1.py').read_bytes()).hexdigest()}
if __name__=='__main__':
 result=main()
 with Path('experiments/sparse_round_price_component_v1_2026-10-18/differential_validation.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(result))
