from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import test_normalized_rc_net_pressure as fixture
from normalized_rc_net_pressure import NormalizedRCNetPressure
from fast_normalized_rc_net_pressure import FastNormalizedRCNetPressure
class FastNetPressureTests(unittest.TestCase):
 def test_full_result_and_exact_context_hash(self):
  g,p=fixture.NetRCPressureTests().inputs();args=(g,fixture.blend.TEXT,g.sha256,p,100)
  slow=NormalizedRCNetPressure(*args);fast=FastNormalizedRCNetPressure(*args)
  for budget in (0,1,2,3,7):
   slow.base.node_budget=fast.base.node_budget=budget
   for net,source in [(0,10),(1,70)]:
    for sinks in (set(),{50},{50,60}):
     for exclude in (False,True):self.assertEqual(slow.query(net,source,sinks,exclude),fast.query(net,source,sinks,exclude))
 def test_no_query_aliases(self):
  g,p=fixture.NetRCPressureTests().inputs();fast=FastNormalizedRCNetPressure(g,fixture.blend.TEXT,g.sha256,p)
  a,c=fast.query(0,10,{50,60});a.paths.clear();b,d=fast.query(0,10,{50,60});self.assertEqual(set(b.paths),{50,60});self.assertEqual(c,d)
if __name__=='__main__':unittest.main()
