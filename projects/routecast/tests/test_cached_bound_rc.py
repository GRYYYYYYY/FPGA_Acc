from pathlib import Path
import sys,unittest,random
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from cached_bound_rc import CachedBoundRC
from bound_indexed_cost import BoundNormalizedRCBase
import test_bound_indexed_cost as fixture

class CacheTests(unittest.TestCase):
 def test_random_physics_and_indices_exact_all_arcs(self):
  rng=random.Random(20261004)
  for multi in (False,True):
   for _ in range(30):
    g,t,c,b=fixture.BindingTests().inputs(multi);g=replace(g,nodes={n:replace(v,timing=(('R',str(rng.randrange(6))),('C',str(rng.randrange(6))))) for n,v in g.nodes.items()})
    a=BoundNormalizedRCBase(g,t,c,b,100);fast=CachedBoundRC(g,t,c,b,100);self.assertEqual(a.outgoing,fast.outgoing);self.assertEqual(fast.edge_cost_queries,len(g.edges))
 def test_repeated_classes_and_disabled_arcs(self):
  g,t,c,b=fixture.BindingTests().inputs(True);g=replace(g,nodes={n:replace(v,capacity=0 if n==90 else v.capacity) for n,v in g.nodes.items()})
  ref=BoundNormalizedRCBase(g,t,c,b);fast=CachedBoundRC(g,t,c,b);self.assertEqual(fast.outgoing,ref.outgoing);self.assertEqual(fast.edge_cost_queries,len(g.edges));self.assertLess(fast.cache_entries,len(g.edges));self.assertEqual(fast.outgoing[20][-1][-1],None)
 def test_nonbuffered_and_negative_rejected(self):
  g,t,c,b=fixture.BindingTests().inputs()
  with self.assertRaises(ValueError):CachedBoundRC(replace(g,switches={5:'<switch id="5" type="pass_gate"><timing/></switch>'}),t,c,b)
  nodes=dict(g.nodes);nodes[20]=replace(nodes[20],timing=(('R','100'),('C','0')));nodes[30]=replace(nodes[30],capacity=0,timing=(('R','0'),('C','0')))
  with self.assertRaisesRegex(ValueError,'negative RC'):CachedBoundRC(replace(g,nodes=nodes,switches={5:'<switch id="5" type="mux"><timing Cinternal="1"/></switch>'}),t,c,b)
if __name__=='__main__':unittest.main()
