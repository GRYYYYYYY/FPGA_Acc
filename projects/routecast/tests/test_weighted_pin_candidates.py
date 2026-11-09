import random,unittest
from dataclasses import replace
from rr_graph import RREdge
from test_pin_choice_catalog import CatalogTests
from weighted_pin_candidates import WeightedPins
class WeightedTests(unittest.TestCase):
 def test_exhaustive_simple_paths(self):
  g=CatalogTests().fixture(True)
  g=replace(g,edges=g.edges+(RREdge(7,3,0,()),))
  engine=WeightedPins(g);rng=random.Random(20261005)
  for _ in range(200):
   costs=[rng.randrange(8) for e in g.edges];result=engine.query(0,6,0,costs);expected={}
   def visit(n,seen,cost,last_pin=None):
    if n==6:
     expected[last_pin]=min(expected.get(last_pin,cost),cost);return
    for eid in engine.outgoing[n]:
     dest=g.edges[eid].sink
     if dest in seen or (n==0 and dest not in {1,7}):continue
     pin=int(dict(g.nodes[dest].location)['ptc']) if g.nodes[dest].type=='IPIN' else last_pin
     visit(dest,seen|{dest},cost+costs[eid],pin)
   visit(0,{0},0)
   self.assertEqual(result['costs'],expected)
 def test_invalid_costs(self):
  e=WeightedPins(CatalogTests().fixture())
  for costs in ([0]*7,[True]*8,[-1]*8):
   with self.assertRaises(ValueError):e.query(0,6,0,costs)

 def test_longer_path_and_channel_cycle(self):
  g=CatalogTests().fixture();nodes=dict(g.nodes);nodes[8]=replace(nodes[3],id=8)
  g=replace(g,nodes=nodes,edges=g.edges+(RREdge(1,8,0,()),RREdge(8,3,0,()),RREdge(3,8,0,())))
  costs=[0]*len(g.edges);costs[2]=100;costs[8]=1;costs[9]=1
  result=WeightedPins(g).query(0,6,0,costs)
  self.assertEqual(result['costs'],{0:2,1:2})
  for path in result['paths'].values():self.assertIn(8,path);self.assertIn(9,path);self.assertNotIn(10,path)

 def test_blocked_channel_and_validation(self):
  e=WeightedPins(CatalogTests().fixture());self.assertEqual(e.query(0,6,0,[0]*8,{3})['paths'],{})
  for blocked in ({0},{True},{99}):
   with self.assertRaises(ValueError):e.query(0,6,0,[0]*8,blocked)

 def test_blocked_edges_exhaustive_and_validation(self):
  g=CatalogTests().fixture(True);engine=WeightedPins(g);rng=random.Random(20261006)
  for _ in range(200):
   costs=[rng.randrange(8) for e in g.edges];blocked={i for i in range(len(g.edges)) if rng.randrange(3)==0};expected={}
   def visit(n,seen,cost,pin=None):
    if n==6:expected[pin]=min(expected.get(pin,cost),cost);return
    for eid in engine.outgoing[n]:
     dest=g.edges[eid].sink
     if eid in blocked or dest in seen or (n==0 and dest not in {1,7}):continue
     nextpin=int(dict(g.nodes[dest].location)['ptc']) if g.nodes[dest].type=='IPIN' else pin
     visit(dest,seen|{dest},cost+costs[eid],nextpin)
   visit(0,{0},0);result=engine.query(0,6,0,costs,blocked_edges=blocked);self.assertEqual(result['costs'],expected)
   self.assertTrue(all(not set(path)&blocked for path in result['paths'].values()))
  for blocked in ({True},{-1},{len(g.edges)}):
   with self.assertRaises(ValueError):engine.query(0,6,0,[0]*len(g.edges),blocked_edges=blocked)

 def test_requested_pin_costs_paths_equal_full_search(self):
  g=CatalogTests().fixture(True);nodes=dict(g.nodes);nodes[8]=replace(nodes[3],id=8)
  g=replace(g,nodes=nodes,edges=g.edges+(RREdge(1,8,0,()),RREdge(8,3,0,()),RREdge(3,8,0,())))
  engine=WeightedPins(g);rng=random.Random(20261007)
  for _ in range(200):
   costs=[rng.randrange(8) for e in g.edges];blocked={i for i in range(len(g.edges)) if rng.randrange(5)==0};full=engine.query(0,6,0,costs,blocked_edges=blocked)
   for targets in ({0},{1},{0,1}):
    partial=engine.query(0,6,0,costs,blocked_edges=blocked,target_pins=targets)
    self.assertEqual(partial['costs'],{p:c for p,c in full['costs'].items() if p in targets})
    self.assertEqual(partial['paths'],{p:path for p,path in full['paths'].items() if p in targets})
  for targets in (set(),{True},{-1},{99}):
   with self.assertRaises(ValueError):engine.query(0,6,0,[0]*len(g.edges),target_pins=targets)
