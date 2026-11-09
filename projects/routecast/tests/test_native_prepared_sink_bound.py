import unittest
from fractions import Fraction as F
from array import array
from test_integer_rc_budget_boundaries import IntegerBudgetBoundaries
from native_integer_rc_prepared_sink_bound import NativeIntegerRCPreparedSinkBound
from native_integer_rc_sink_bound import NativeIntegerRCSinkBound
from rc_feasible_cost_region import RCFeasibleCostRegion
class PointerTests(unittest.TestCase):
 def test_copy_once_and_query_results_match_dense_bound_wrapper(self):
  rc,integer,costs=IntegerBudgetBoundaries().graph([(0,3,10,F(1,7)),(0,1,1,F(1,7)),(1,2,1,F(1,7))]);f=integer.fields;f['costs']=costs;f['capacities']=[1]*4;region=RCFeasibleCostRegion(4,[(u,f['dest_ranks'][i],integer.increments[i],costs[i]) for u in range(4) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])]);remaining=region.distance(3,True)
  class Bounds:
   nodes=4;calls=0
   def get(self,sink):
    if sink!=3:raise ValueError('unknown sink')
    self.calls+=1;return memoryview(array('Q',[remaining.get(n,(1<<64)-1) for n in range(4)]).tobytes()).cast('Q')
  bounds=Bounds();prepared=NativeIntegerRCPreparedSinkBound(integer,bounds);dense=NativeIntegerRCSinkBound(integer)
  for budget,limit in ((integer.scale,3),(0,1),(integer.scale,100)):
   self.assertEqual(prepared.query(0,3,budget,limit),dense.query_bound(0,3,budget,remaining,limit))
  self.assertEqual(bounds.calls,1);self.assertEqual(len(prepared.bound_arrays),1)
  with self.assertRaises(ValueError):prepared.query(0,2,integer.scale)
  with self.assertRaises(ValueError):prepared.query_bound(0,3,integer.scale,remaining)
if __name__=='__main__':unittest.main()
