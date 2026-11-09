from pathlib import Path
import sys,unittest,random
from dataclasses import replace
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from tree_reuse import TreeReuse
from astar_tree_reuse import AStarTreeReuse
from frozen_tree_pressure import FrozenTreePressure
from normalized_rc_pressure import NormalizedRCPressureSketch
import test_normalized_rc_net_pressure as fixture
import test_normalized_rc_base as blend

class FrozenTreeTests(unittest.TestCase):
 def test_materialized_costs_and_own_trunk_once(self):
  g,p=fixture.NetRCPressureTests().inputs();m=FrozenTreePressure(g,blend.TEXT,g.sha256,p,100)
  self.assertEqual(m.demand[30],2);self.assertEqual(m.penalties(0,10)[30],200)
  contexts=[]
  for net,source,sinks in ((0,10,{50,60}),(1,70,{50})):
   demand={n:v-(n in m.users[net]) for n,v in m.demand.items()}
   material=NormalizedRCPressureSketch(g,blend.TEXT,g.sha256,demand,g.sha256,100);weights=[None]*len(g.edges)
   for arcs in material.outgoing.values():
    for eid,dst,w in arcs:weights[eid]=w
   expected=TreeReuse(g,weights,m.engine.timing).route(source,sinks);actual,context=m.route(net,source,sinks)
   self.assertEqual((actual.paths,actual.parents,actual.failures),(expected.paths,expected.parents,expected.failures));contexts.append(context)
  self.assertNotEqual(*contexts);self.assertEqual(m.route(0,10,{50,60})[1],contexts[0])
  p['node_occupancy']['30']=99
  self.assertEqual(m.demand[30],2)
  with self.assertRaises(ValueError):m.route(0,70,{50})
 def test_random_destination_cost_reference(self):
  g=fixture.NetRCPressureTests().inputs()[0];rng=random.Random(20261006)
  for _ in range(100):
   weights=[rng.randrange(1,25) for e in g.edges];timing=[Fraction(rng.randrange(30),3) for e in g.edges];penalties={n:rng.randrange(15) for n in g.nodes}
   expected=TreeReuse(g,[w+penalties[e.sink] for w,e in zip(weights,g.edges)],timing).route(10,{50,60});actual=AStarTreeReuse(g,weights,timing).route(10,{50,60},penalties)
   self.assertEqual((actual.paths,actual.parents,actual.failures),(expected.paths,expected.parents,expected.failures))
 def test_bad_penalties_and_background(self):
  g,p=fixture.NetRCPressureTests().inputs();m=FrozenTreePressure(g,blend.TEXT,g.sha256,p,100)
  for penalties in ({30:-1},{30:True},{999:1}):
   with self.assertRaises(ValueError):m.engine.route(10,{50},penalties)
  p['node_occupancy']['30']=3
  with self.assertRaises(ValueError):FrozenTreePressure(g,blend.TEXT,g.sha256,p,100)

if __name__=='__main__':unittest.main()
