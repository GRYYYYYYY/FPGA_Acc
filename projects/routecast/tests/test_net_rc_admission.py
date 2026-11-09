import unittest
from fractions import Fraction as F
from net_rc_admission import admit_rc_net

class RCAdmissionTests(unittest.TestCase):
    def test_whole_net_and_exact_boundary(self):
        baseline={1:F(1),2:F(2)}
        self.assertTrue(admit_rc_net(baseline,dict(baseline))['accepted'])
        self.assertEqual(admit_rc_net(baseline,{1:F(0),2:F(2)+F(1,10**40)}),{'accepted':False,'failing_connections':[2]})
        self.assertEqual(baseline,{1:F(1),2:F(2)})
    def test_invalid_complete_cohort(self):
        for baseline,candidate in [({},{}),({1:F(1)},{}),({1:F(1)},{1:1.0}),({1:F(1)},{1:F(-1)})]:
            with self.assertRaises(ValueError):admit_rc_net(baseline,candidate)
if __name__=='__main__':unittest.main()
