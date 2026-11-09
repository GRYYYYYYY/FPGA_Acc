import sys,unittest,itertools
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from exact_channel_twins_v1 import Builder
class Contract(unittest.TestCase):
 def test_exhaustive_three_node_graphs(self):
  arcs=[(u,v,0) for u in range(3) for v in range(3) if u!=v]
  for mask in range(1<<len(arcs)):
   edges=[e for i,e in enumerate(arcs) if mask>>i&1];b=Builder()
   for n in range(3):b.node(n,('CHANX',1))
   for e in edges:b.edge(*e)
   for group in b.classes():
    for perm in itertools.permutations(group):
     p=dict(zip(group,perm));self.assertEqual(Counter(edges),Counter((p.get(u,u),p.get(v,v),s) for u,v,s in edges))
    for n in group[1:]:b.verify_swap(group[0],n)
 def test_switch_multiplicity_metadata_and_incoming_guards(self):
  good=[(0,2,0),(0,3,0),(2,4,1),(3,4,1)]
  for mode in ['ok','switch','multiplicity','incoming','metadata']:
   b=Builder();b.node(2,('CHANX',1));b.node(3,('CHANY',1) if mode=='metadata' else ('CHANX',1));edges=list(good)
   if mode=='switch':edges[-1]=(3,4,2)
   if mode=='multiplicity':edges.append(edges[-1])
   if mode=='incoming':edges[1]=(1,3,0)
   for e in edges:b.edge(*e)
   self.assertEqual(bool(b.classes()),mode=='ok')
 def test_whole_path_and_capacity_transport(self):
  edges=[(u,v,0) for u in [0,1] for v in [2,3]]+[(u,v,1) for u in [2,3] for v in [4,5]];b=Builder()
  for n in [2,3]:b.node(n,('CHANX',1))
  for e in edges:b.edge(*e)
  self.assertEqual(b.classes(),[(2,3)]);b.verify_swap(2,3);edge_pairs={(u,v) for u,v,s in edges}
  for paths in [[(0,2,4)],[(0,2,4),(1,3,5)]]:
   mapped=[tuple(3 if n==2 else 2 if n==3 else n for n in path) for path in paths]
   for old,new in zip(paths,mapped):
    self.assertEqual((old[0],old[-1]),(new[0],new[-1]));self.assertTrue(all(e in edge_pairs for e in zip(new,new[1:])))
   counts=Counter(n for p in mapped for n in set(p));self.assertTrue(all(counts[n]<=1 for n in [2,3]))
if __name__=='__main__':unittest.main()
