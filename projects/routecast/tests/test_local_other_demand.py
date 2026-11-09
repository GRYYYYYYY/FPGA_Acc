import random,unittest
from collections import Counter
from local_other_demand import LocalOtherDemand
class Native:
 def __init__(self):self.other=Counter({99:7});self.previous={99};self.demand_epoch=0
 def apply_other(self,epoch,updates):
  assert epoch==self.demand_epoch
  for n,v in updates:
   if v:self.other[n]=v
   else:self.other.pop(n,None)
  self.previous=set(self.other);self.demand_epoch+=1
class TestLocal(unittest.TestCase):
 def test_random_accept_reject_and_stage_restart(self):
  rng=random.Random(17);unions=[set(rng.sample(range(100),12)) for _ in range(9)];native=Native();local=LocalOtherDemand(native);dirty=set()
  for step in range(500):
   if step%73==0:local=LocalOtherDemand(native)
   occ=Counter(n for u in unions for n in u);net=step%9
   local.transition(occ,unions[net],dirty)
   expected=occ.copy();expected.subtract(unions[net]);expected=+expected
   self.assertEqual(local.values,dict(expected));self.assertEqual(native.other,expected)
   old=unions[net];new=set(rng.sample(range(100),rng.randrange(1,18)))
   if rng.randrange(3):unions[net]=new;dirty=old^new
   else:dirty=set()
 def test_failed_native_publication(self):
  native=Native();local=LocalOtherDemand(native);old=dict(local.values)
  def fail(*args):raise RuntimeError('capture failure')
  native.apply_other=fail
  with self.assertRaises(RuntimeError):local.transition(Counter({1:1}),{1})
  self.assertEqual(local.values,old);self.assertIsNone(local.excluded)
