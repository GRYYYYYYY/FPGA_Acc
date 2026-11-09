import sys,unittest,itertools
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from exact_channel_twins_v1 import Builder
from anchored_channel_refinement_v1 import initial,step,summary
class Contract(unittest.TestCase):
 def make(self,metadata,edges):
  b=Builder()
  for n,m in metadata.items():b.node(n,m)
  for e in edges:b.edge(*e)
  return b
 def test_all64_directed_three_node_graph_automorphisms(self):
  arcs=[(u,v,0) for u in range(3) for v in range(3) if u!=v]
  for mask in range(64):
   edges=[e for i,e in enumerate(arcs) if mask>>i&1];b=self.make({i:'same' for i in range(3)},edges);c=initial(b.meta)
   for _ in range(3):
    c=step(c,b.out,b.inc)
    for p in itertools.permutations(range(3)):
     if Counter(edges)==Counter((p[u],p[v],s) for u,v,s in edges):self.assertTrue(all(c[n]==c[p[n]] for n in c))
 def test_coupled_symmetry_survives_without_local_twins(self):
  edges=[(0,1,0),(0,2,0),(1,3,0),(2,4,0),(3,7,0),(4,7,0)];b=self.make({1:'A',2:'A',3:'B',4:'B'},edges)
  self.assertEqual(b.classes(),[]);c=initial(b.meta)
  for _ in range(4):c=step(c,b.out,b.inc)
  self.assertEqual(c[1],c[2]);self.assertEqual(c[3],c[4]);self.assertEqual(summary(c)['unresolved_channels'],4)
  p={1:2,2:1,3:4,4:3};self.assertEqual(Counter(edges),Counter((p.get(u,u),p.get(v,v),s) for u,v,s in edges))
 def test_anchored_distinction_propagates_two_hops(self):
  edges=[(0,1,0),(0,2,0),(1,3,0),(2,4,0),(3,7,0),(4,7,0),(8,3,0)];b=self.make({1:'A',2:'A',3:'B',4:'B'},edges);c=initial(b.meta)
  c=step(c,b.out,b.inc);self.assertEqual(c[1],c[2]);self.assertNotEqual(c[3],c[4]);c=step(c,b.out,b.inc);self.assertEqual(summary(c)['unresolved_channels'],0)
 def test_switch_direction_multiplicity_and_metadata_preserved(self):
  for edges in [[(0,1,0),(0,2,1)],[(0,1,0),(2,0,0)],[(0,1,0),(0,2,0),(0,2,0)]]:
   b=self.make({1:'A',2:'A'},edges);c=step(initial(b.meta),b.out,b.inc);self.assertNotEqual(c[1],c[2])
  b=self.make({1:'A',2:'B'},[]);self.assertNotEqual(initial(b.meta)[1],initial(b.meta)[2])
if __name__=='__main__':unittest.main()
