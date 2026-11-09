import unittest
from test_integer_rc_budget_boundaries import IntegerBudgetBoundaries
from native_integer_rc_search import NativeIntegerRC
from csr_integer_budget_search import query
from fractions import Fraction as F

class NativeRCSearchTests(unittest.TestCase):
 def test_budget_eligibility_limits_and_counters(self):
  rc,scaled,costs=IntegerBudgetBoundaries().graph([(0,1,3,F(1,7)),(0,2,0,F(1,3)),(1,3,3,F(1,7)),(2,3,0,F(1,3))])
  scaled.fields['costs']=costs;scaled.fields['capacities']=[1]*4
  native=NativeIntegerRC(scaled)
  for other in ({},{1:2,3:1},{}):
   native.set_other(other)
   for budget in [0,scaled.encode(rc.path(0,3,[0,2])),scaled.scale]:
    for limit in [1,3,100]:
     expected=query(scaled,0,3,budget,lambda u,i:True,lambda u,i:costs[i]*(1+other.get(scaled.fields['dest_ranks'][i],0)),limit)
     self.assertEqual(native.query(0,3,budget,limit),expected)
 def test_invalid_demand_preserves_previous(self):
  rc,scaled,costs=IntegerBudgetBoundaries().graph([(0,3,1,F(1,7))]);scaled.fields['costs']=costs;scaled.fields['capacities']=[1]*4;native=NativeIntegerRC(scaled);native.set_other({3:1});before=native.query(0,3,scaled.scale)
  with self.assertRaises(ValueError):native.set_other({3:-1})
  self.assertEqual(native.query(0,3,scaled.scale),before)
 def test_arithmetic_exhaustion_is_not_unreachable(self):
  rc,scaled,costs=IntegerBudgetBoundaries().graph([(0,1,(1<<64)-2,F(1,7)),(1,3,(1<<64)-2,F(1,7))]);scaled.fields['costs']=costs;scaled.fields['capacities']=[1]*4
  native=NativeIntegerRC(scaled);native.set_other({1:(1<<64)-1,3:(1<<64)-1})
  result=native.query(0,3,scaled.scale)
  self.assertEqual(result['status'],'ARITHMETIC_LIMIT');self.assertIsNone(result['physical_edge_ids'])
  native.set_other({});scaled.initial=lambda node:(1<<128)-1
  result=native.query(0,3,(1<<128)-1)
  self.assertEqual(result['status'],'ARITHMETIC_LIMIT');self.assertIsNone(result['delay'])
 def test_demand_single_capture_and_iteration_failure(self):
  rc,scaled,costs=IntegerBudgetBoundaries().graph([(0,3,1,F(1,7))]);scaled.fields['costs']=costs;scaled.fields['capacities']=[1]*4;native=NativeIntegerRC(scaled)
  class Once:
   calls=0
   def items(self):
    self.calls+=1
    if self.calls!=1:raise AssertionError('repeated input traversal')
    return iter([(3,2),(1,0)])
  demand=Once();native.set_other(demand);self.assertEqual(demand.calls,1)
  before=list(native.other);previous=native.previous.copy();result=native.query(0,3,scaled.scale)
  class Broken:
   def items(self):
    yield 3,4
    raise RuntimeError('incomplete demand snapshot')
  with self.assertRaises(RuntimeError):native.set_other(Broken())
  for invalid in ({4:0},{True:0},{1:False},{1:1<<64}):
   with self.assertRaises(ValueError):native.set_other(invalid)
  self.assertEqual(list(native.other),before);self.assertEqual(native.previous,previous);self.assertEqual(native.query(0,3,scaled.scale),result)
  native.set_other({});self.assertEqual(list(native.other),[0]*4)
if __name__=='__main__':unittest.main()
