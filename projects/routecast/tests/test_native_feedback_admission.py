import unittest
from fractions import Fraction as F
from native_feedback_admission import decide

class FeedbackAdmissionTest(unittest.TestCase):
 def setUp(self):
  self.b={'success':True,'physical_verified':True,'context_sha256':'a'*64,'timing_scope_sha256':'b'*64}
  self.c={**self.b,'cpd_ns':F(3),'wirelength':100,'full_pipeline_s':F(1),'route_sha256':'c'*64,'measurement_receipt_sha256':'d'*64}
 def run_gate(self):return decide(self.b,self.c,cpd_limit=F(3),wirelength_limit=100,pipeline_limit=F(1))
 def test_equality_accepted_and_each_budget_independently_rejected(self):
  self.assertEqual(self.run_gate()['status'],'ACCEPT')
  for key,v in [('cpd_ns',F(3)+F(1,10**30)),('wirelength',101),('full_pipeline_s',F(1)+F(1,10**30))]:
   old=self.c[key];self.c[key]=v;self.assertIn('exceeds_'+key,self.run_gate()['reasons']);self.c[key]=old
 def test_missing_full_time_and_context_mismatch_reject(self):
  self.c['full_pipeline_s']=None;self.c['timing_scope_sha256']='e'*64
  r=self.run_gate();self.assertEqual(r['status'],'REJECT');self.assertIn('missing_full_pipeline_s',r['reasons']);self.assertIn('mismatched_timing_scope_sha256',r['reasons'])
 def test_failure_not_qor_and_failed_baseline_not_normalized(self):
  self.c['success']=False;self.c['physical_verified']=False
  self.assertIn('candidate_route_failed',self.run_gate()['reasons'])
  self.b['success']=False;self.assertEqual(self.run_gate()['status'],'INSUFFICIENT_BASELINE')
if __name__=='__main__':unittest.main()
