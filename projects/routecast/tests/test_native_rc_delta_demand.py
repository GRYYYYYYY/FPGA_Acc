import unittest
from fractions import Fraction as F
from test_integer_rc_budget_boundaries import IntegerBudgetBoundaries
from native_integer_rc_delta_demand import NativeIntegerRCDeltaDemand
from native_integer_rc_sparse_trace import NativeIntegerRCSparseTrace

class DeltaTests(unittest.TestCase):
 def test_absolute_updates_delete_and_full_reset(self):
  rc,scaled,costs=IntegerBudgetBoundaries().graph([(0,1,1,F(1,7)),(1,3,2,F(1,7))]);scaled.fields['costs']=costs;scaled.fields['capacities']=[1]*4
  delta=NativeIntegerRCDeltaDemand(scaled);full=NativeIntegerRCSparseTrace(scaled)
  for other,updates in (({1:2},[(1,2)]),({1:2,3:1},[(3,1)]),({3:1},[(1,0)]),({3:1},[])):
   old=delta.demand_epoch;self.assertEqual(delta.apply_other(old,updates),old+1);full.set_other(other)
   self.assertEqual(delta.traced_query(0,3,scaled.scale),full.traced_query(0,3,scaled.scale));self.assertEqual(delta.previous,set(other))
  delta.set_other({});full.set_other({});self.assertEqual(delta.query(0,3,scaled.scale),full.query(0,3,scaled.scale))
 def test_stale_invalid_and_interrupted_capture_preserve_state(self):
  rc,scaled,costs=IntegerBudgetBoundaries().graph([(0,3,1,F(1,7))]);scaled.fields['costs']=costs;scaled.fields['capacities']=[1]*4;delta=NativeIntegerRCDeltaDemand(scaled);delta.apply_other(0,[(3,2)]);before=(list(delta.other),delta.previous.copy(),delta.demand_epoch)
  def broken():
   yield 3,4
   raise RuntimeError('incomplete delta')
  with self.assertRaises(RuntimeError):delta.apply_other(1,broken())
  for epoch,updates in ((0,[(3,0)]),(True,[]),(1,[(3,3),(3,0)]),(1,[(3,-1)]),(1,[(True,0)]),(1,[(4,0)]),(1,[(2,1<<64)])):
   with self.assertRaises(ValueError):delta.apply_other(epoch,updates)
   self.assertEqual((list(delta.other),delta.previous,delta.demand_epoch),before)
if __name__=='__main__':unittest.main()
