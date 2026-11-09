import sys,unittest,tempfile,json,copy,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from mmc_model_lifetime_v1 import Controller
class Contract(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/'state';self.p.write_text('{}');self.released=[]
 def tearDown(self):self.tmp.cleanup()
 def generator(self,bindings=None):
  try:
   yield {'kind':'ready','bindings':bindings or {},'resources':(1,2)}
   for i in range(2):
    self.p.write_text(json.dumps({'round':i,'rows':[i]}));yield {'kind':'round','index':i,'file':str(self.p),'resources':(1,2)}
   return {'done':True}
  finally:self.released.append(True)
 def test_order_stale_tickets_detached_reads_and_export(self):
  m=Controller(self.generator());ready=m.current
  with self.assertRaises(ValueError):m.export(ready)
  with self.assertRaises(ValueError):m.step(ready,1)
  a=m.step(ready,0)
  with self.assertRaises(RuntimeError):m.read_state(ready)
  with self.assertRaises(RuntimeError):m.step(copy.copy(a),1)
  state=m.read_state(a);state['rows'][0]=99;self.assertEqual(m.read_state(a)['rows'],[0])
  b=m.step(a,1)
  with self.assertRaises(RuntimeError):m.read_state(a)
  self.assertTrue(m.export(b)['done']);self.assertEqual(self.released,[True])
  with self.assertRaises(RuntimeError):m.step(b,1)
 def test_early_close_releases_owner_once(self):
  m=Controller(self.generator());t=m.current;m.close();m.close();self.assertEqual(self.released,[True])
  with self.assertRaises(RuntimeError):m.step(t,0)
 def test_changed_input_closes_before_update(self):
  digest=hashlib.sha256(self.p.read_bytes()).hexdigest();m=Controller(self.generator({str(self.p):digest}));self.p.write_text('[]')
  with self.assertRaises(ValueError):m.step(m.current,0)
  self.assertEqual(self.released,[True]);self.assertEqual(m.phase,'CLOSED')
 def test_state_file_rewrite_is_detected(self):
  m=Controller(self.generator());t=m.step(m.current,0);self.p.write_text('{}')
  with self.assertRaises(ValueError):m.read_state(t)
  m.close()
if __name__=='__main__':unittest.main()
