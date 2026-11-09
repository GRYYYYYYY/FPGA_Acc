import unittest
from fractions import Fraction
from net_quality_admission import admit_net

class AdmissionTest(unittest.TestCase):
 def test_complete_net_rejected_if_single_delay_or_cost_regresses(self):
  old={0:{'scalar':10,'delay':Fraction(1,10)},1:{'scalar':20,'delay':Fraction(1,5)}}
  new={0:{'scalar':9,'delay':Fraction(1,10)},1:{'scalar':20,'delay':Fraction(1,5)+Fraction(1,10**30)}}
  self.assertEqual(admit_net(old,new),{'accepted':False,'failing_connections':[1]})
  new[1]={'scalar':21,'delay':Fraction(1,6)}
  self.assertFalse(admit_net(old,new)['accepted'])
  new[1]={'scalar':20,'delay':Fraction(1,5)}
  self.assertTrue(admit_net(old,new)['accepted'])
 def test_missing_cohort_and_float_delay_rejected(self):
  old={0:{'scalar':10,'delay':Fraction(1)}}
  with self.assertRaises(ValueError):admit_net(old,{})
  with self.assertRaises(ValueError):admit_net(old,{0:{'scalar':10,'delay':1.0}})
if __name__=='__main__':unittest.main()
