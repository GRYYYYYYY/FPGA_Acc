"""Adversarial bounded-search dependency replay across small cyclic graphs."""
import random,unittest
from fractions import Fraction as F
from test_integer_rc_budget_boundaries import IntegerBudgetBoundaries
from native_integer_rc_sparse_trace import NativeIntegerRCSparseTrace
from native_integer_rc_search import NativeIntegerRC
from csr_integer_budget_search import query
from rc_read_dependency_cache import RCReadDependencyCache
from rc_read_dependency_cache_direct_restore import DirectRestoreRCReadDependencyCache

class DependencyReplayTests(unittest.TestCase):
 def test_changed_unread_demands_preserve_full_bounded_execution(self):
  rng=random.Random(2026100601);statuses=set();hits=0;status_counts={}
  for case in range(150):
   edges=[(u,v,rng.randrange(6),F(rng.randrange(4),7)) for u in range(6) for v in range(6) if rng.random()<.24]
   rc,scaled,costs=IntegerBudgetBoundaries().graph(edges,6);f=scaled.fields;f['costs']=costs;f['capacities']=[rng.randrange(3) for _ in range(6)]
   # Disabled edges and zero-capacity nodes must not become demand dependencies.
   for i in range(len(costs)):
    if rng.random()<.1:costs[i]=(1<<64)-1
   native=NativeIntegerRCSparseTrace(scaled);plain=NativeIntegerRC(scaled);other={n:rng.randrange(4) for n in range(6)};budget=rng.randrange(2*scaled.scale);limit=rng.choice((1,2,3,7,100));source=rng.randrange(6);sink=rng.randrange(6)
   reads=set()
   def cost(u,i):
    v=f['dest_ranks'][i]
    if costs[i]>0:reads.add(v)
    return costs[i]*(1+other[v])
   expected=query(scaled,source,sink,budget,lambda u,i:costs[i]!=(1<<64)-1 and f['capacities'][f['dest_ranks'][i]]>0,cost,limit)
   native.set_other(other);plain.set_other(other);result,footprint=native.traced_query(source,sink,budget,limit);self.assertEqual(result,expected);self.assertEqual(result,plain.query(source,sink,budget,limit));self.assertEqual(footprint,frozenset(reads));statuses.add(result['status']);status_counts[result['status']]=status_counts.get(result['status'],0)+1
   cache=RCReadDependencyCache(6);context='a'*64;self.assertTrue(cache.store(case,context,other,footprint,result));cache=DirectRestoreRCReadDependencyCache.restore(6,cache.payload())
   for _ in range(4):
    changed={n:other[n] if n in footprint else rng.randrange(100) for n in range(6)}
    cached=cache.lookup(case,context,changed);self.assertIsNotNone(cached);native.set_other(changed);new,newreads=native.traced_query(source,sink,budget,limit);self.assertEqual(new,result);self.assertEqual(new,cached[0]);self.assertEqual(newreads,footprint);hits+=1
   if footprint:
    node=min(footprint);changed=dict(other);changed[node]+=1;self.assertIsNone(cache.lookup(case,context,changed))
  self.assertEqual(hits,600);self.assertGreaterEqual(statuses,{'FOUND','UNREACHABLE','LABEL_LIMIT'});self.report={'seed':2026100601,'graphs':150,'unchanged_read_demand_mutations':hits,'baseline_status_counts':status_counts,'full_native_python_baseline_parity':150,'all_full_replay_results_and_read_sets_equal':True}
if __name__=='__main__':unittest.main()
