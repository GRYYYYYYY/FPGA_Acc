import unittest
from types import SimpleNamespace
from rr_graph import RREdge
from tree_rc import TreeRC

def fixture(kind='pass_gate',internal=0):
 nodes={n:SimpleNamespace(timing=(('R',str(r)),('C',str(c)))) for n,(r,c) in enumerate(((10,1),(0,2),(0,3)))}
 xml=f'<switch type="{kind}"><timing R="0" Tdel="0" Cinternal="{internal}"/></switch>'
 return SimpleNamespace(nodes=nodes,edges=(RREdge(0,1,0,()),RREdge(0,2,0,()),RREdge(1,2,0,()),RREdge(2,1,0,())),switches={0:xml})
class TreeRCTests(unittest.TestCase):
 def test_unbuffered_branch_load(self):
  oracle=TreeRC(fixture());both=oracle.evaluate(0,[0,1]);self.assertEqual(both['downstream_capacitance'][0],6);self.assertEqual(dict(both['delay_seconds']),{0:30,1:30,2:30});self.assertEqual(oracle.evaluate(0,[0])['delay_seconds'][1],15)
 def test_buffer_isolates_load_but_internal_cap_remains(self):
  self.assertEqual(dict(TreeRC(fixture('buffer')).evaluate(0,[0,1])['delay_seconds']),{0:5,1:5,2:5})
  self.assertEqual(TreeRC(fixture('buffer',4)).evaluate(0,[0,1])['delay_seconds'][1],45)
 def test_edge_resistance_and_intrinsic_delay(self):
  g=fixture('buffer');g.switches={0:'<switch type="buffer"><timing R="7" Tdel="11"/></switch>'};r=TreeRC(g).evaluate(0,[0,1]);self.assertEqual(r['delay_seconds'][1],30);self.assertEqual(r['delay_seconds'][2],37)
 def test_invalid_tree_and_identity(self):
  oracle=TreeRC(fixture())
  for source,edges in ((0,[0,1,2]),(0,[2,3]),(1,[0]),(True,[]),(0,[True]),(0,[-1]),(0,[4])):
   with self.assertRaises(ValueError):oracle.evaluate(source,edges)
  self.assertEqual(oracle.evaluate(0,[0,0])['edge_count'],1)
