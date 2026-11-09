import unittest
from dataclasses import replace
from rr_graph import RRGraph,RRNode,RREdge
from pin_choice_catalog import PinChoiceCatalog
class CatalogTests(unittest.TestCase):
 def fixture(self,facets=False):
  kinds=['SOURCE','OPIN','OPIN','CHANX','IPIN','IPIN','SINK'];ptcs=[0,0,1,0,0,1,0]
  nodes={i:RRNode(i,k,2 if k in {'SOURCE','SINK'} else 1,'NONE',(),(('ptc',str(ptcs[i])),),(),None) for i,k in enumerate(kinds)};arcs=[(0,1),(0,2),(1,3),(2,3),(3,4),(3,5),(4,6),(5,6)]
  if facets:nodes[7]=replace(nodes[1],id=7);arcs.append((0,7))
  return RRGraph(nodes,tuple(RREdge(a,b,0,()) for a,b in arcs),{}, {},{},'g')
 def test_facets_distinct_from_physical_pin_count(self):
  c=PinChoiceCatalog(self.fixture(True));self.assertEqual(len(c.sources[0].physical_pins),2);self.assertEqual(c.sources[0].physical_pins[0],(1,7));self.assertEqual(c.witness(0,6,[0,2,4,6])['selected_ipin_rr'],4)
 def test_same_class_two_different_pin_witnesses(self):
  c=PinChoiceCatalog(self.fixture());a=c.witness(0,6,[0,2,4,6]);b=c.witness(0,6,[1,3,5,7]);self.assertEqual(a['sink_class'],b['sink_class']);self.assertNotEqual(a['selected_ipin_ptc'],b['selected_ipin_ptc'])
 def test_bad_membership_and_witness_reject(self):
  g=self.fixture();nodes=dict(g.nodes);nodes[0]=replace(nodes[0],capacity=3)
  with self.assertRaises(ValueError):PinChoiceCatalog(replace(g,nodes=nodes))
  c=PinChoiceCatalog(g)
  for path in ([0,7],None,[True]):
   with self.assertRaises(ValueError):c.witness(0,6,path)
  with self.assertRaises(TypeError):c.sources[0].physical_pins[2]=(99,)
