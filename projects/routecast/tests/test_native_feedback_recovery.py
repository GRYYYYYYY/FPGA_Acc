import unittest
from fractions import Fraction as F
from native_feedback_admission import decide_recovery

class RecoveryTest(unittest.TestCase):
 def setUp(self):
  self.b={'success':False,'failure_verified':True,'context_sha256':'a'*64,'timing_scope_sha256':'b'*64}
  self.c={'success':True,'physical_verified':True,'context_sha256':'a'*64,'timing_scope_sha256':'b'*64,'cpd_ns':F(3),'wirelength':100,'full_pipeline_s':F(2),'route_sha256':'c'*64,'measurement_receipt_sha256':'d'*64}
  self.k={'protocol_sha256':'e'*64,'context_sha256':'a'*64,'timing_scope_sha256':'b'*64,'cpd_limit':F(3),'wirelength_limit':100,'pipeline_limit':F(2)}
 def test_success_can_recover_without_inventing_baseline_qor(self):
  self.assertEqual(decide_recovery(self.b,self.c,self.k)['status'],'ACCEPT')
  self.assertNotIn('cpd_ns',self.b)
 def test_success_without_contract_is_not_accepted(self):
  self.assertEqual(decide_recovery(self.b,self.c,None)['status'],'INSUFFICIENT_BUDGET')
 def test_failed_candidate_is_rejected_even_without_budget(self):
  self.c['success']=False;self.c['physical_verified']=False
  self.assertEqual(decide_recovery(self.b,self.c,None)['status'],'REJECT')
 def test_absolute_budget_and_context_are_enforced(self):
  self.c['full_pipeline_s']=F(2)+F(1,10**30)
  self.assertIn('exceeds_full_pipeline_s',decide_recovery(self.b,self.c,self.k)['reasons'])
  self.k['context_sha256']='f'*64
  self.assertIn('mismatched_recovery_contract',decide_recovery(self.b,self.c,self.k)['reasons'])
if __name__=='__main__':unittest.main()
