import unittest
from tree_rc import TreeRC
from buffered_delay_cost import BufferedDelayCost
from test_tree_rc import fixture
class BufferedDelayTests(unittest.TestCase):
 def test_exact_tree_path_equality_with_branching(self):
  g=fixture('buffer');g.switches={0:'<switch type="buffer"><timing R="0.7" Tdel="0.11"/></switch>'};cost=BufferedDelayCost(g);tree=TreeRC(g).evaluate(0,[0,1]);self.assertEqual(cost.path_delay(0,[0]),tree['delay_seconds'][1]);self.assertEqual(cost.path_delay(0,[1]),tree['delay_seconds'][2]);self.assertTrue(all(type(w) is int and w>=0 for w in cost.weights))
 def test_unsupported_electrical_semantics_rejected(self):
  for graph in (fixture(),fixture('buffer',1)):
   with self.assertRaises(ValueError):BufferedDelayCost(graph)
 def test_invalid_paths(self):
  cost=BufferedDelayCost(fixture('buffer'))
  for source,edges in ((True,[]),(0,[True]),(0,[2]),(0,[0,2,3])):
   with self.assertRaises(ValueError):cost.path_delay(source,edges)

 def test_cache_keeps_switch_identity_and_exact_decimal_metadata(self):
  from dataclasses import replace
  from types import SimpleNamespace
  g=fixture('buffer');g.nodes[2]=SimpleNamespace(timing=(('R','0.0'),('C','2.0')));g.switches[1]='<switch type="buffer"><timing R="3" Tdel="0"/></switch>';g.edges=(g.edges[0],replace(g.edges[1],switch_id=1),*g.edges[2:]);cost=BufferedDelayCost(g)
  self.assertEqual(cost.path_delay(0,[0]),5);self.assertEqual(cost.path_delay(0,[1]),11)
