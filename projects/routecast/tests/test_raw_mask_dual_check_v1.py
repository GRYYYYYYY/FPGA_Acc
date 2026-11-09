import sys,unittest
from pathlib import Path
from array import array
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from raw_mask_dual_check_v1 import Checker
B=Path(__file__).resolve().parents[1]/'experiments/mmc_cover_budget_avoidance_v1_2026-10-21/raw_dual_check.so'
class Contract(unittest.TestCase):
 def test_primal_dual_and_rejected_potential(self):
  c=Checker(B);args=[array('I',[0,1]),array('I',[1,2]),array('Q',[2,3]),array('I',[1]*3),array('Q',[0,2,5]),bytearray([1]*3),bytearray(3),0,0,5,False]
  self.assertEqual(c.check(*args),2);args[4][2]=6;args[9]=6
  with self.assertRaises(ValueError):c.check(*args)
 def test_deleted_node_and_closed_reachability_cut(self):
  c=Checker(B);args=[array('I',[0,1]),array('I',[1,2]),array('Q',[2,3]),array('I',[1]*3),array('Q',[0,0,0]),bytearray([1,0,0]),bytearray([0,1,0]),0,0,0,True];self.assertEqual(c.check(*args),0)
  args[6][1]=0
  with self.assertRaises(ValueError):c.check(*args)
 def test_addition_uses_wide_arithmetic(self):
  top=2**64-1;c=Checker(B);self.assertEqual(c.check(array('I',[0]),array('I',[1]),array('Q',[5]),array('I',[1,1]),array('Q',[top-1,top]),bytearray([1,1]),bytearray(2),0,top-1,top,False),1)
if __name__=='__main__':unittest.main()
