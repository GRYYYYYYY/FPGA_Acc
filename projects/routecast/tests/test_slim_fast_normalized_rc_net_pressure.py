from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import test_normalized_rc_net_pressure as fixture
from fast_normalized_rc_net_pressure import FastNormalizedRCNetPressure
from slim_fast_normalized_rc_net_pressure import SlimFastNormalizedRCNetPressure
from model_object_size import reachable_size
class SlimTests(unittest.TestCase):
 def test_exact_query_and_smaller_reachable_size(self):
  g,p=fixture.NetRCPressureTests().inputs();args=(g,fixture.blend.TEXT,g.sha256,p,100)
  fast=FastNormalizedRCNetPressure(*args);slim=SlimFastNormalizedRCNetPressure(*args)
  self.assertFalse(hasattr(slim.base,'outgoing'))
  for budget in (0,1,2,7):
   fast.base.node_budget=slim.base.node_budget=budget
   for net,source in [(0,10),(1,70)]:
    for exclude in (True,False):self.assertEqual(fast.query(net,source,{50,60},exclude),slim.query(net,source,{50,60},exclude))
  self.assertLess(reachable_size(slim,(g,p)),reachable_size(fast,(g,p)))
 def test_size_deduplicates_and_excludes(self):
  shared=[object()];self.assertEqual(reachable_size([shared,shared],(shared,)),sys.getsizeof([shared,shared]))
if __name__=='__main__':unittest.main()
