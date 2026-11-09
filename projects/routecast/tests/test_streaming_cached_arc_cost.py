import random
import unittest
from dataclasses import replace
from fractions import Fraction
from test_bound_indexed_cost import BindingTests
from cached_bound_rc import CachedBoundRC
from streaming_cached_arc_cost import StreamingCachedArcCost

class StreamingArcTests(unittest.TestCase):
    def test_all_arc_parity_random_physics_and_disabled(self):
        rng=random.Random(20261005)
        for multi in (False,True):
            for _ in range(30):
                g,t,c,b=BindingTests().inputs(multi)
                g=replace(g,nodes={n:replace(v,capacity=0 if rng.randrange(8)==0 else v.capacity,
                    timing=(('R',str(rng.randrange(10))),('C',str(rng.randrange(10))))) for n,v in g.nodes.items()})
                old=CachedBoundRC(g,t,c,b,100)
                new=StreamingCachedArcCost(g.switches,{i:r['base'] for i,r in old.rows.items()},old.normalization,100)
                for arcs in old.outgoing.values():
                    for eid,dest,expected in arcs:
                        edge=g.edges[eid];a=dict(g.nodes[edge.source].timing);z=dict(g.nodes[dest].timing)
                        self.assertEqual(new.cost(edge.switch_id,a['R'],z['R'],z['C'],old.indices[dest],g.nodes[dest].capacity),expected)
                self.assertEqual(new.queries,len(g.edges))
    def test_signed_internal_rounding_and_invalid(self):
        switch={0:'<switch type="mux"><timing Cinternal="1"/></switch>'}
        e=StreamingCachedArcCost(switch,{0:1},1,1)
        with self.assertRaisesRegex(ValueError,'negative RC'):e.cost(0,100,0,0,0,0)
        e=StreamingCachedArcCost({0:'<switch type="mux"><timing/></switch>'},{0:1},1,1)
        self.assertEqual(e.cost(0,0,0,0,0),0) # exact tie-to-even 0.5
        for args in ((True,0,0,0,0),(0,-1,0,0,0),(0,0,0,0,True),(0,0,0,0,0,True)):
            with self.assertRaises(ValueError):e.cost(*args)
        for kwargs in ({'normalization':0},{'scale':True},{'bases':{True:1}}):
            a=dict(switches={0:'<switch type="mux"><timing/></switch>'},bases={0:1},normalization=1);a.update(kwargs)
            with self.assertRaises(ValueError):StreamingCachedArcCost(**a)
