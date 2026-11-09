from pathlib import Path
import sys,unittest,random
from fractions import Fraction
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from tree_reuse import TreeReuse
from astar_tree_reuse import AStarTreeReuse
from rr_graph import read_rr_graph,RREdge
class AStarTests(unittest.TestCase):
 def graph(self):
  g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml');return replace(g,edges=g.edges+(RREdge(20,40,5,()),RREdge(30,60,5,()),RREdge(40,30,5,())))
 def test_random_exact_paths_parents_failures(self):
  rng=random.Random(20261005);g=self.graph()
  for _ in range(200):
   weights=[rng.randrange(5,25) for e in g.edges];timing=[Fraction(rng.randrange(20),3) for e in g.edges]
   model=AStarTreeReuse(g,weights,timing);self.assertGreater(model.alpha,0)
   ref=TreeReuse(g,weights,timing).route(10,{50,60});fast=model.route(10,{50,60})
   self.assertEqual((ref.paths,ref.parents,ref.failures),(fast.paths,fast.parents,fast.failures))
 def test_consistency_for_both_targets(self):
  g=self.graph();weights=[17]*len(g.edges);model=AStarTreeReuse(g,weights,[1]*len(g.edges));self.assertGreater(model.alpha,0)
  for target in (50,60):
   h=model.heuristic(target);self.assertEqual(h(target),0)
   for eid,e in enumerate(g.edges):
    if g.nodes[e.sink].type=='SINK' and e.sink!=target:continue
    self.assertLessEqual(h(e.source),weights[eid]+h(e.sink))
 def test_zero_cost_movement_fallback_and_terminal_rejection(self):
  g=self.graph();model=AStarTreeReuse(g,[0]*len(g.edges),[0]*len(g.edges));self.assertEqual(model.alpha,0)
  with self.assertRaises(ValueError):AStarTreeReuse(replace(g,edges=g.edges+(RREdge(50,40,5,()),)),[1]*(len(g.edges)+1),[0]*(len(g.edges)+1))
if __name__=='__main__':unittest.main()
