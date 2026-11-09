from pathlib import Path
import sys,unittest
from fractions import Fraction as F
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from normalized_rc_base import NormalizedRCBaseSketch
from path_rc import PathRC
import test_native_indexed_cost as base_test
TEXT=base_test.TEXT
class NormalizedBlendTests(unittest.TestCase):
 def graph(self):
  g=base_test.NativeCostTests().graph()
  return replace(g,nodes={n:replace(v,timing=(('R','4'),('C','3'))) for n,v in g.nodes.items()})
 def test_dimension_and_rounding(self):
  g=self.graph();engine=NormalizedRCBaseSketch(g,TEXT,g.sha256,100);rc=PathRC(g)
  costs={'SOURCE':F(1),'SINK':F(0),'OPIN':F(1),'IPIN':F(95,100),'CHANX':F(4),'CHANY':F(4)}
  for arcs in engine.outgoing.values():
   for eid,dst,w in arcs:
    exact=(rc.path(g.edges[eid].source,[eid]).delay+costs[g.nodes[dst].type])/2
    self.assertEqual(w,round(exact*100))
    self.assertLessEqual(abs(F(w,100)-exact),F(1,200))
  # Switching time units and the normalization consistently preserves weights.
  nodes={n:replace(v,timing=(('R','4'),('C','0.003'))) for n,v in g.nodes.items()}
  switches={5:'<switch id="5" type="mux"><timing Tdel="1e-13"/></switch>'}
  g2=replace(g,nodes=nodes,switches=switches)
  text=TEXT.replace('factor: 1','factor: 0.001').replace('SOURCE 1 ','SOURCE 0.001 ').replace('OPIN 1 ','OPIN 0.001 ').replace('IPIN 0.95 ','IPIN 0.00095 ').replace('test 4 ','test 0.004 ')
  self.assertEqual(engine.outgoing,NormalizedRCBaseSketch(g2,text,g2.sha256,100).outgoing)
 def test_graph_identity_and_resistance_restriction(self):
  g=self.graph()
  with self.assertRaises(ValueError):NormalizedRCBaseSketch(g,TEXT,'wrong')
  with self.assertRaises(ValueError):NormalizedRCBaseSketch(replace(g,switches={5:'<switch id="5" type="pass_gate"><timing/></switch>'}),TEXT,g.sha256)
if __name__=='__main__':unittest.main()
