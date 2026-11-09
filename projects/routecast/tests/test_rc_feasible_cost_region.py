import unittest,random
from rc_feasible_cost_region import RCFeasibleCostRegion
class RegionTests(unittest.TestCase):
 def test_every_feasible_walk_edge_is_retained(self):
  rng=random.Random(2206)
  for _ in range(80):
   edges=[(u,v,rng.randint(1,3),rng.randint(0,5)) for u in range(3) for v in range(3) if rng.randrange(2)]
   graph=RCFeasibleCostRegion(3,edges);budget=rng.randint(1,7);initial=rng.randint(0,2);region=graph.destinations(0,2,initial,budget);used=set()
   def walk(u,delay,positive):
    if u==2:used.update(positive)
    for a,b,d,c in edges:
     if a==u and delay+d<=budget:walk(b,delay+d,positive|({b} if c else set()))
   if initial<=budget:walk(0,initial,set())
   self.assertLessEqual(used,region)
 def test_zero_delay_cycles_and_impossible_budget(self):
  graph=RCFeasibleCostRegion(3,[(0,1,0,1),(1,0,0,1),(1,2,1,1)])
  self.assertEqual(graph.destinations(0,2,0,1),frozenset({0,1,2}));self.assertEqual(graph.destinations(0,2,2,1),frozenset())
 def test_prefix_includes_budget_rejected_arc_reads(self):
  graph=RCFeasibleCostRegion(3,[(0,1,0,1),(1,2,100,1)])
  self.assertEqual(graph.destinations(0,2,0,1),frozenset())
  self.assertEqual(graph.prefix_destinations(0,0,1),frozenset({1,2}))
  self.assertEqual(graph.prefix_destinations(0,2,1),frozenset())
if __name__=='__main__':unittest.main()
