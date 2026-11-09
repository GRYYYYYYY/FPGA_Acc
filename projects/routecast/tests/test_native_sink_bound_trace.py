import random,unittest
from array import array
from fractions import Fraction as F
from test_integer_rc_budget_boundaries import IntegerBudgetBoundaries
from native_integer_rc_sink_bound_trace import NativeIntegerRCSinkBoundTrace
from native_integer_rc_sink_bound import NativeIntegerRCSinkBound
from csr_integer_sink_bound_search import query
from rc_feasible_cost_region import RCFeasibleCostRegion
class TraceTests(unittest.TestCase):
 def test_full_results_reads_and_mixed_query_reset(self):
  rng=random.Random(2026100603)
  for _ in range(80):
   edges=[(u,v,rng.randrange(6),F(rng.randrange(3),7)) for u in range(6) for v in range(6) if rng.random()<.2];rc,integer,costs=IntegerBudgetBoundaries().graph(edges,6);f=integer.fields;f['costs']=costs;f['capacities']=[rng.randrange(3) for _ in range(6)]
   region=RCFeasibleCostRegion(6,[(u,f['dest_ranks'][i],integer.increments[i],costs[i]) for u in range(6) for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if f['capacities'][f['dest_ranks'][i]]>0]);remaining=region.distance(5,True)
   class Bounds:
    nodes=6
    def get(self,sink):return memoryview(array('Q',[remaining.get(n,(1<<64)-1) for n in range(6)]).tobytes()).cast('Q')
   traced=NativeIntegerRCSinkBoundTrace(integer,Bounds());plain=NativeIntegerRCSinkBound(integer);other={n:rng.randrange(4) for n in range(6)};traced.set_other(other);plain.set_other(other)
   for budget,limit in ((0,1),(integer.scale,2),(2*integer.scale,100)):
    reads=set()
    def cost(u,i):
     v=f['dest_ranks'][i]
     if costs[i]>0:reads.add(v)
     return costs[i]*(1+other[v])
    expected=query(integer,0,5,budget,lambda u,i:f['capacities'][f['dest_ranks'][i]]>0,cost,remaining,limit)
    traced.query(0,5,budget,limit);actual,footprint=traced.traced_query(0,5,budget,limit)
    self.assertEqual(actual,expected);self.assertEqual(actual,plain.query_bound(0,5,budget,remaining,limit));self.assertEqual(footprint,frozenset(reads))
 def test_objective_overflow_marks_last_read(self):
  rc,integer,costs=IntegerBudgetBoundaries().graph([(0,1,(1<<64)-2,F(1,7)),(1,3,(1<<64)-2,F(1,7))]);f=integer.fields;f['costs']=costs;f['capacities']=[1]*4
  region=RCFeasibleCostRegion(4,[(u,f['dest_ranks'][i],integer.increments[i],costs[i]) for u in range(4) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])]);remaining=region.distance(3,True)
  class Bounds:
   nodes=4
   def get(self,sink):return memoryview(array('Q',[remaining.get(n,(1<<64)-1) for n in range(4)]).tobytes()).cast('Q')
  traced=NativeIntegerRCSinkBoundTrace(integer,Bounds());plain=NativeIntegerRCSinkBound(integer);demand={1:(1<<64)-1,3:(1<<64)-1};traced.set_other(demand);plain.set_other(demand)
  result,reads=traced.traced_query(0,3,integer.scale);self.assertEqual(result,plain.query_bound(0,3,integer.scale,remaining));self.assertEqual(result['status'],'ARITHMETIC_LIMIT');self.assertEqual(reads,frozenset({1,3}))
if __name__=='__main__':unittest.main()
