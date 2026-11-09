"""Bellman oracle, exact old-budget-bound search parity and cache isolation."""
import random,json,hashlib,copy
from pathlib import Path
from fractions import Fraction
from compact_target_raw_bounds_v1 import CompactReverseBounds,MAX_CAP
from reverse_raw_delay_bounds_v1 import ReverseBounds
from weighted_budget_pareto_search_v1 import search
R=Path(__file__).resolve().parents[1];D=R/'experiments/compact_target_raw_bounds_contract_v1_2026-10-20'
def csr(n,arcs):
 offsets=[0];dest=[];raw=[]
 for u in range(n):
  for a,v,w in arcs:
   if a==u:dest.append(v);raw.append(w)
  offsets.append(len(dest))
 return offsets,dest,raw

def oracle(n,arcs,target):
 values=[None]*n;values[target]=0
 for _ in range(n-1):
  changed=False
  for u,v,w in arcs:
   if values[v] is not None and (values[u] is None or w+values[v]<values[u]):values[u]=w+values[v];changed=True
  if not changed:break
 return values

def main():
 D.mkdir(exist_ok=False);rng=random.Random(20261020);bound_checks=search_checks=0;evictions=growth=0;wide=set()
 for trial in range(120):
  n=rng.randrange(2,10);arcs=[(u,v,rng.randrange(10)) for u in range(n) for v in range(n) if rng.random()<.3]
  if arcs:arcs.append(arcs[0])
  offsets,dest,raw=csr(n,arcs);original=ReverseBounds(offsets,dest,raw);ceilings={t:13 for t in range(0,n,2)};cache=CompactReverseBounds(offsets,dest,raw,max_cache_bytes=n*2,target_budget_ceilings=ceilings);assert cache.context==original.context;saved=[]
  for target in range(n):
   truth=oracle(n,arcs,target)
   for budget in [0,1,9,3,20,2,50,256,2**32+5,2**64+3,MAX_CAP-1]:
    view=cache.bound(target,budget);old=original.bound(target,budget);values=tuple(view.get(u) for u in range(n));expected=tuple(budget+1 if v is None else min(v,budget+1) for v in truth);assert values==expected==old.values;assert view.context==old.context and view.cap==old.cap and view.target==old.target;assert cache.cached_bytes<=cache.limit;wide.add(view._packed.width);bound_checks+=1
    if budget in [0,MAX_CAP-1]:saved.append((view,values))
  assert all(tuple(view.get(u) for u in range(n))==values for view,values in saved)
  for _ in range(6):
   target=rng.randrange(n);budget=rng.randrange(1,40);caps=[rng.randrange(2) for _ in range(n)];caps[0]=1;initial={0:0};prices={u:rng.randrange(11) for u in range(n)};criticality=rng.choice([Fraction(0),Fraction(1,2),Fraction(1)]);limit=rng.choice([1,10000]);before=copy.deepcopy((caps,initial,prices));a=search(offsets,dest,raw,caps,initial,target,criticality,prices,budget,original.bound(target,budget),max_labels=limit);b=search(offsets,dest,raw,caps,initial,target,criticality,prices,budget,cache.bound(target,budget),max_labels=limit);assert a==b and before==(caps,initial,prices);search_checks+=1
  view=cache.bound(0,10);expected=tuple(view.get(u) for u in range(n));offsets[0]=1
  if dest:dest[0]=n+10;raw[0]=999
  assert tuple(cache.bound(0,10).get(u) for u in range(n))==expected
  evictions+=cache.evictions;growth+=cache.growth_rebuilds
 offsets,dest,raw=csr(4,[(0,1,1<<127),(1,2,(1<<127)-1)]);cache=CompactReverseBounds(offsets,dest,raw,max_cache_bytes=1024);view=cache.bound(2,MAX_CAP-1);assert view.get(0)==MAX_CAP-1 and view.get(3)==MAX_CAP and view._packed.width==17;wide.add(17)
 ro=CompactReverseBounds([0,1,1],[1],[1],max_cache_bytes=100).bound(1,10)
 try:ro._packed._view[0]=7
 except TypeError:pass
 else:raise AssertionError('packed data writable')
 invalid=0
 for args in [([1,1],[0],[1]),([0,1,1],[2],[1]),([0,1,1],[1],[-1]),([0,1,1],[1],[True])]:
  try:CompactReverseBounds(*args)
  except ValueError:invalid+=1
  else:raise AssertionError('bad CSR accepted')
 for target,budget in [(4,0),(0,-1),(0,MAX_CAP),(False,1)]:
  try:cache.bound(target,budget)
  except ValueError:invalid+=1
  else:raise AssertionError('bad query accepted')
 assert evictions>0 and growth>0 and wide=={1,2,4,8,16,17}
 files=[Path(__file__),R/'tools/compact_target_raw_bounds_v1.py',R/'tools/reverse_raw_delay_bounds_v1.py',R/'tools/weighted_budget_pareto_search_v1.py'];result=dict(status='BELLMAN_EXACT_CAP_VIEWS_AND_ORIGINAL_SEARCH_PARITY_COMPACT_LRU_PASS',random_graphs=120,bound_queries=bound_checks,masked_price_context_searches=search_checks,payload_widths_bytes=sorted(wide),LRU_evictions_exercised=evictions,growth_rebuilds_exercised=growth,invalid_inputs_rejected=invalid,old_views_survive_growth_and_eviction=True,caller_CSR_cost_mutations_do_not_change_owned_context=True,packed_values_read_only=True,bindings={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Cache views exactly match legacy perbudget bounds, including complete search status/path/work counters. Not parity to zero heuristic, real-cohort speed or forecast quality. Retained payload limit only.')
 (D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
