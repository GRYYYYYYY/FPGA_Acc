import unittest
from verify_rc_remaining_certificate import verify,U64
class RemainingTests(unittest.TestCase):
 def fields(self):return dict(node_ids=list(range(4)),row_offsets=[0,1,2,3,3],edge_ids=[0,1,2],dest_ranks=[1,0,3],costs=[1]*3,capacities=[1]*4)
 def test_zero_cycle_fake_reachability_rejected(self):
  f=self.fields();self.assertTrue(verify(f,[0,0,2],3,[U64,U64,2,0])['all_distance_and_tight_path_checks_passed'])
  with self.assertRaises(ValueError):verify(f,[0,0,2],3,[0,0,2,0])
 def test_inequality_tight_path_and_unreachable(self):
  f=dict(node_ids=[0,1],row_offsets=[0,1,1],edge_ids=[0],dest_ranks=[1],costs=[1],capacities=[1,1])
  self.assertEqual(verify(f,[2],1,[2,0])['finite_nodes'],2)
  for values in ([1,0],[3,0],[U64,0],[2,1],[True,0]):
   with self.assertRaises(ValueError):verify(f,[2],1,values)
if __name__=='__main__':unittest.main()
