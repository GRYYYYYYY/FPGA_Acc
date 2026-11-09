from pathlib import Path
import sys,random,unittest
from types import SimpleNamespace
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from exact_goal_astar import ExactGoalAStar
from compact_indexed_sketch import CompactIndexedSketch
from rr_graph import read_rr_graph,RREdge
class GoalTests(unittest.TestCase):
 def test_random_full_budget_canonical_paths_and_consistency(self):
  g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml');g=replace(g,edges=g.edges+(RREdge(20,40,5,()),RREdge(30,60,5,()),RREdge(40,30,5,())))
  rng=random.Random(20261004)
  for iteration in range(100):
   engine=CompactIndexedSketch(g,node_budget=len(g.nodes));weights=[0 if iteration%10==0 else rng.randrange(1,40) for e in g.edges];engine.outgoing={n:tuple((eid,dst,weights[eid]) for eid,dst,w in arcs) for n,arcs in engine.outgoing.items()};a=ExactGoalAStar(engine)
   for targets in ({50},{60},{50,60}):
    self.assertEqual(a.search(10,targets).paths,engine.search(10,targets).paths);h=a.heuristic(targets)
    for eid,e in enumerate(g.edges):self.assertLessEqual(h(e.source),weights[eid]+h(e.sink))
 def test_fallback_budget_and_terminal_contract(self):
  g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml');engine=CompactIndexedSketch(g,node_budget=len(g.nodes));a=ExactGoalAStar(engine);self.assertEqual(a.heuristic(set(range(17)))(10),0)
  engine.node_budget=1
  with self.assertRaises(ValueError):ExactGoalAStar(engine)
  bad=dict(a.outgoing);bad[50]=((0,10,1),)
  with self.assertRaises(ValueError):ExactGoalAStar(SimpleNamespace(graph=g,outgoing=bad,node_budget=len(g.nodes)))
 def test_frozen_snapshot(self):
  g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml');engine=CompactIndexedSketch(g,node_budget=len(g.nodes));a=ExactGoalAStar(engine);old=a.search(10,{50});engine.outgoing[10]=();self.assertEqual(a.search(10,{50}),old)
if __name__=='__main__':unittest.main()
