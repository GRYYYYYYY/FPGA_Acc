import unittest
from dataclasses import replace
from test_pin_choice_catalog import CatalogTests
from reachable_pin_candidates import ReachablePins

class ReachabilityTests(unittest.TestCase):
 def test_all_pins_and_fixed_output(self):
  g=CatalogTests().fixture(True);r=ReachablePins(g).query(0,6,0)
  self.assertEqual(set(r['paths']),{0,1})
  for path in r['paths'].values():self.assertEqual(g.edges[path[0]].sink,1)
 def test_unreachable_member_and_disabled_channel(self):
  g=CatalogTests().fixture();g=replace(g,edges=tuple(e for e in g.edges if (e.source,e.sink)!=(3,5)))
  self.assertEqual(set(ReachablePins(g).query(0,6,0)['paths']),{0})
  nodes=dict(g.nodes);nodes[3]=replace(nodes[3],capacity=0)
  self.assertEqual(ReachablePins(replace(g,nodes=nodes)).query(0,6,0)['paths'],{})
 def test_invalid_pin(self):
  with self.assertRaises(ValueError):ReachablePins(CatalogTests().fixture()).query(0,6,True)
