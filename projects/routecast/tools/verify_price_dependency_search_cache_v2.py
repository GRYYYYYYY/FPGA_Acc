"""Actual skipped searches against uncached hybrid; deterministic requested paths."""
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
import random,json,hashlib
from price_dependency_search_cache_v2 import Search as Cached
from hybrid_bidirectional_search_v1 import Search as Original
R=Path(__file__).resolve().parents[1];O=R/'experiments/price_dependency_search_cache_contract_v2_2026-10-10';O.mkdir(exist_ok=True)
def canonical(answer,source):
 raw,parents,found=answer;paths={}
 for t in sorted(found):
  u=t;p=[]
  while u!=source:
   prev,e=parents[u];p.append(e);u=prev;assert len(p)<1000
  paths[t]=(raw[t],tuple(reversed(p)))
 return paths
counts=Counter()
for seed in range(200):
 rng=random.Random(seed);n=rng.randrange(3,30);f=dict(row_offsets=[0],dest_ranks=[],capacities=[1]*n);inc=[]
 for u in range(n):
  for v in range(n):
   if rng.random()<.12 or v==(u+1)%n:f['dest_ranks'].append(v);inc.append(rng.choice([0,0,1,7,2**40]))
  f['row_offsets'].append(len(inc))
 rc=SimpleNamespace(increments=inc,initial=lambda u:u%5);a=Original(f,rc,R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so');b=Cached(f,rc,entries=3);bounded=Cached(f,rc,entries=3,read_limit=0);small=Cached(f,rc,entries=3,output_limit=0)
 for step in range(12):
  src=rng.randrange(n);targets={rng.randrange(n)} if step%2 else set(rng.sample(range(n),rng.randrange(n+1)));weight=[0,1,17,2**63][step%4];prices={u:rng.randrange(8) for u in range(n)}
  for s in [a,b,bounded,small]:s.prepare(prices,weight)
  ref=canonical(a.search(src,targets),src);ans=b.search(src,targets);assert canonical(ans,src)==ref
  for s in [bounded,small]:assert canonical(s.search(src,targets),src)==ref
  # Deep output isolation, then a real hit that bypasses both native calls.
  ans[0].clear();ans[1].clear();ans[2].clear();h=b.stats['hits'];assert canonical(b.search(src,targets),src)==ref;assert b.stats['hits']==h+1;counts['hits_checked']+=1
  key=(src,tuple(sorted(targets)),weight);d=dict(b.cache[key][0]);changed={u:prices[u] if u in d else prices[u]+9 for u in range(n)}
  a.prepare(changed,weight);b.prepare(changed,weight);h=b.stats['hits'];assert canonical(b.search(src,targets),src)==canonical(a.search(src,targets),src)==ref;assert b.stats['hits']==h+1;counts['unread_change_hits']+=1
  if d:
   changed[min(d)]+=3;a.prepare(changed,weight);b.prepare(changed,weight);m=b.stats['misses'];assert canonical(b.search(src,targets),src)==canonical(a.search(src,targets),src);assert b.stats['misses']==m+1;counts['observed_change_misses']+=1
  # Every following step is a fresh query after skips; exercise error then recovery too.
  if step%3==0:
   try:b.search(src,{n})
   except (RuntimeError,AssertionError):counts['invalid_target_recovery']+=1
   else:raise AssertionError('invalid target accepted')
   assert canonical(b.search(src,targets),src)==canonical(a.search(src,targets),src)
  counts['queries']+=1
 for name,s in [('cache',b),('bounded',bounded),('small_output',small)]:
  counts.update({name+'_'+k:v for k,v in s.stats.items()});assert len(s.cache)<=3 and s.dependency_items==sum(len(v[0]) for v in s.cache.values()) and s.output_items==sum(sum(len(x) for x in v[1]) for v in s.cache.values());s.close()
 # Force global dependency/output limits below each complete entry.
 tiny=Cached(f,rc,dependency_total_limit=0,output_total_limit=0)
 tiny.prepare({},1);assert canonical(tiny.search(0,{1}),0)==canonical((lambda: (a.prepare({},1),a.search(0,{1}))[1])(),0)
 assert not tiny.cache and tiny.dependency_items==tiny.output_items==0;counts['total_limit_fallbacks']+=1;tiny.close()
 a.close()
 # Invalid prepares preserve the prior successful logical price context.
 # Tested with a fresh instance because b was deliberately closed above.
 c=Cached(f,rc);c.prepare({},1);expected=canonical(c.search(0,{1}),0)
 for price,weight in [({0:-1},1),({0:2**64-1},2**64-1),({},-1)]:
  try:c.prepare(price,weight)
  except ValueError:counts['failed_prepare_preservation']+=1
  else:raise AssertionError('invalid prepare accepted')
  assert canonical(c.search(0,{1}),0)==expected
 c.close()
 # Close prohibits a stale cached result.
 try:b.search(0,{0})
 except RuntimeError:counts['closed_rejections']+=1
 else:raise AssertionError('closed accepted')
assert counts['hits_checked']==2400 and counts['cache_evictions']>0 and counts['bounded_incomplete']>0 and counts['small_output_oversize_output']>0
B=R/'build/price_read_trace_v2_2026-10-10';v=json.loads((B/'receipt.json').read_text());bindings={**v['inputs'],**v['outputs']}
for name in ['verify_price_dependency_search_cache_v2.py','price_dependency_search_cache_v2.py','build_price_read_trace_v2.py','hybrid_bidirectional_search_v1.py','soft_demand_cpp_bridge_v1.py','soft_demand_workspace_bridge_v1.py','bidirectional_rc_bridge_v1.py']:
 p=R/'tools'/name;bindings[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in [R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so',R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so']:bindings[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in bindings.items())
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,random_graphs=200,counts=dict(counts),scope='Actual standalone128 requested-result cache skips, sequential hit/miss recovery, deep output isolation, LRU eviction and zero-limit fallbacks vs uncached hybrid. Not native64/live transaction/full pipeline/performance evidence.'),indent=2)+'\n');print(dict(counts))
