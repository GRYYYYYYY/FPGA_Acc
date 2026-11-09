import unittest,tempfile,pathlib
from nonclock_global_pins import classify
class Test(unittest.TestCase):
 def fixture(self,path,pin='dsp.reset[0]',flag='true',ptc=0):
  (path/'net').write_text('<block><block name="b" instance="dsp[0]"/></block>')
  (path/'arch').write_text('<architecture><tiles><tile name="dsp"><sub_tile name="dsp"><equivalent_sites><site pb_type="dsp"/></equivalent_sites><input name="reset" num_pins="1" is_non_clock_global="'+flag+'"/></sub_tile></tile></tiles></architecture>')
  (path/'graph').write_text('<rr_graph><block_types><block_type name="dsp"><pin_class type="INPUT"><pin ptc="0">'+pin+'</pin></pin_class></block_type></block_types><rr_nodes/></rr_graph>')
  return {'pin_details':[{'role':'SINK','block':'b','port':'reset','bit':0,'physical_pin_ptc':ptc,'class_id':0,'net_id':4,'net':'arbitrary_dynamic_signal','rr_node':10}]}
 def test_optional_instance_formats(self):
  for text in ['dsp.reset[0]','dsp[0].reset[0]']:
   with tempfile.TemporaryDirectory() as d:
    p=pathlib.Path(d);m=self.fixture(p,text);r=classify(m,p/'net',p/'arch',p/'graph');self.assertEqual(len(r),1);self.assertEqual(r[0]['net_id'],4)
 def test_explicit_declaration_required(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);m=self.fixture(p,flag='false');self.assertEqual(classify(m,p/'net',p/'arch',p/'graph'),[])
 def test_wrong_physical_binding_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);m=self.fixture(p,ptc=7)
   with self.assertRaises(ValueError):classify(m,p/'net',p/'arch',p/'graph')
if __name__=='__main__':unittest.main()
