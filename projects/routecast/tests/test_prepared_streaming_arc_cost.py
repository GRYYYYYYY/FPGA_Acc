import unittest
from fractions import Fraction
from prepared_streaming_arc_cost import PreparedStreamingArcCost
from test_bound_indexed_cost import BindingTests
from cached_bound_rc import CachedBoundRC
from path_rc import PathRC
class ClassCostTests(unittest.TestCase):
 def test_every_fixture_arc_equal(self):
  for multi in (False,True):
   g,t,c,b=BindingTests().inputs(multi);old=CachedBoundRC(g,t,c,b);rc=PathRC(g);ids=sorted(g.nodes);rank={n:i for i,n in enumerate(ids)}
   m=PreparedStreamingArcCost(g.switches,{i:Fraction(row['base']) for i,row in old.rows.items()},old.normalization,[rc.nodes[n][0] for n in ids],[rc.nodes[n][1] for n in ids],[old.indices[n] for n in ids],[g.nodes[n].capacity for n in ids])
   expected={eid:cost for arcs in old.outgoing.values() for eid,_,cost in arcs}
   for eid,e in enumerate(g.edges):self.assertEqual(m.cost(e.switch_id,rank[e.source],rank[e.sink]),expected[eid])
   self.assertEqual(m.queries,len(g.edges))
 def test_disabled_negative_and_invalid(self):
  switches={0:'<switch id="0" type="buffer"><timing R="0" Tdel="0" Cinternal="1"/></switch>'}
  m=PreparedStreamingArcCost(switches,{0:0},1,[10,0],[0,0],[0,0],[1,0])
  with self.assertRaisesRegex(ValueError,'negative RC'):m.cost(0,0,1)
  for args in ((True,0,1),(0,True,1),(0,0,-1),(1,0,1)):
   with self.assertRaises(ValueError):m.cost(*args)
  with self.assertRaises(ValueError):PreparedStreamingArcCost(switches,{0:0},1,[0],[0],[True],[1])

 def test_random_classes_equal_scalar(self):
  import random
  from streaming_cached_arc_cost import StreamingCachedArcCost
  rng=random.Random(371);switches={0:'<switch id="0" type="mux"><timing R="2" Tdel="0.1" Cinternal="0.01"/></switch>'};bases={0:0,1:Fraction(1,3)}
  r=[Fraction(rng.randrange(5),10) for _ in range(80)];c=[Fraction(rng.randrange(5),100) for _ in r];indices=[rng.randrange(2) for _ in r];caps=[rng.randrange(2) for _ in r]
  m=PreparedStreamingArcCost(switches,bases,Fraction(1,7),r,c,indices,caps);scalar=StreamingCachedArcCost(switches,bases,Fraction(1,7))
  for _ in range(1600):
   a=rng.randrange(80);b=rng.randrange(80);self.assertEqual(m.cost(0,a,b),scalar.cost(0,r[a],r[b],c[b],indices[b],caps[b]))
