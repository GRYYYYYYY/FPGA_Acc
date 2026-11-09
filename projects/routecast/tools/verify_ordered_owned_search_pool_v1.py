"""Native hybrid requested-path parity across bounded independent lanes."""
import json, random, sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from hybrid_bidirectional_search_v1 import Search
from ordered_owned_search_pool_v1 import SearchPool
from freeze_requested_search_result_v1 import freeze_requested
from source_binding_v2 import closure, sha
binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so'
rng=random.Random(41010); comparisons=0
class RC:
 def __init__(self,inc):self.increments=inc
 def initial(self,u):return u%7
for graph_id in range(30):
 n=35; rows=[0];dest=[];inc=[]
 for u in range(n):
  for v in range(n):
   if u!=v and rng.random()<.09:dest.append(v);inc.append(rng.randrange(1,20))
  rows.append(len(dest))
 fields=dict(row_offsets=rows,dest_ranks=dest,capacities=[1]*n);rc=RC(inc)
 factory=lambda:Search(fields,rc,binary)
 serial=factory();pool=SearchPool(factory,workers=2,window=4)
 try:
  for epoch in range(3):
   prices={u:rng.randrange(10) for u in range(n)};serial.prepare(prices,epoch);pool.prepare(prices,epoch)
   queries=[(rng.randrange(n),rng.sample(range(n),rng.randrange(1,5))) for _ in range(40)]
   expected=[]
   for source,targets in queries:
    expected.append(freeze_requested(source,targets,*serial.search(source,targets)))
   assert list(pool.search_many(queries))==expected
   comparisons+=len(queries)
  consumed=[]
  def stream():
   for q in queries:consumed.append(q);yield q
  batch=pool.search_many(stream());next(batch)
  assert len(consumed)==4
  for action in [lambda:pool.prepare({},0),pool.close,lambda:next(pool.search_many(queries))]:
   try:action()
   except RuntimeError:pass
   else:raise AssertionError('active batch guard missing')
  batch.close();assert not pool.active
  assert list(pool.search_many(queries))==expected
  # Invalid native source must propagate without leaving an active batch.
  try:list(pool.search_many([(n,{0}),*queries]))
  except (AssertionError,RuntimeError):pass
  else:raise AssertionError('invalid query accepted')
  assert not pool.active
  pool.prepare({},0)
 finally:pool.close();serial.close()
D=R/'experiments/ordered_owned_search_pool_contract_v1_2026-10-10';D.mkdir()
extra=[binary,R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so']
bindings=closure([Path(__file__)])
bindings.update({str(p):sha(p) for p in extra})
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,random_graphs=30,price_epochs=90,requested_path_comparisons=comparisons,workers=2,pending_window=4,ordered_native_parity=True,bounded_input_consumption=True,early_close_and_error_cleanup=True,scope='Small native graphs only; no MMC fullgraph parity, speedup, transaction integration or fullworkflow gain.'),indent=2)+'\n')
print('PASS',comparisons,'native ordered requested-path comparisons')
