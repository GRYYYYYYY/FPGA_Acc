from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import test_normalized_rc_base as blend_test
from normalized_rc_base import NormalizedRCBaseSketch
from normalized_rc_pressure import NormalizedRCPressureSketch
class PressureBlendTests(unittest.TestCase):
 def test_zero_identity_threshold_and_snapshot(self):
  g=blend_test.NormalizedBlendTests().graph();text=blend_test.TEXT;base=NormalizedRCBaseSketch(g,text,g.sha256,100)
  zero=NormalizedRCPressureSketch(g,text,g.sha256,{},g.sha256,100);self.assertEqual(base.outgoing,zero.outgoing)
  demand={30:1,40:99};one=NormalizedRCPressureSketch(g,text,g.sha256,demand,g.sha256,100);demand[30]=100
  for n,arcs in one.outgoing.items():
   for (_,dst,w),(_,_,old) in zip(arcs,base.outgoing[n]):self.assertEqual(w-old,200 if dst==30 else 0)
  self.assertEqual(one.demand[30],1)
  with self.assertRaises(TypeError):one.demand[30]=2
  changed=NormalizedRCPressureSketch(g,text,g.sha256,{30:2},g.sha256,100);self.assertNotEqual(one.context_sha256,changed.context_sha256)
 def test_bad_context(self):
  g=blend_test.NormalizedBlendTests().graph();text=blend_test.TEXT
  for demand in ({30:-1},{30:True},{'30':1},{999:1}):
   with self.assertRaises(ValueError):NormalizedRCPressureSketch(g,text,g.sha256,demand,g.sha256)
  with self.assertRaises(ValueError):NormalizedRCPressureSketch(g,text,g.sha256,{},'wrong')
if __name__=='__main__':unittest.main()
