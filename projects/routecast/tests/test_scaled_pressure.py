from pathlib import Path
import sys,unittest,random
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from frozen_pressure_sketch import FrozenPressureSketch
from scaled_pressure_sketch import ScaledPressureSketch
from fractions import Fraction
from math import ceil
from semantic_sketch import Sketch
from rr_graph import RRGraph,RRNode,RREdge,read_rr_graph
from connection_golden import Edge
from test_connection_golden import exhaustive_path

class ScaledPressureTests(unittest.TestCase):
    def test_random_weighted_paths_against_exhaustive(self):
        rng=random.Random(20261006)
        for case in range(50):
            count=rng.randrange(2,7);nodes={n:RRNode(n,'SOURCE' if n==0 else 'SINK' if n==count-1 else 'CHANX',rng.randrange(1,4),'NONE',(),(('xlow','0'),('ylow','0'),('xhigh','0'),('yhigh','0')),(),None) for n in range(count)}
            edges=tuple(RREdge(rng.randrange(count),rng.randrange(count),5,()) for _ in range(12));g=RRGraph(nodes,edges,{5:'<switch type="mux"><timing Tdel="0"/></switch>'},{},{},'fixture');d={n:rng.randrange(1025) for n in nodes};alpha=7;scale=256
            expected=[]
            for e in edges:
                node=nodes[e.sink];c=node.capacity;channel=node.type=='CHANX';penalty=ceil(alpha*max(Fraction(0),Fraction(d[e.sink],scale)-c+1)/c) if channel else 0
                expected.append(Edge(e.source,e.sink,1+(256 if channel else 0)+penalty))
            result=ScaledPressureSketch(g,d,g.sha256,alpha,count+1,scale).search(0,{count-1})
            self.assertEqual(result.paths.get(count-1),exhaustive_path(count,expected,0,count-1,count-1))
    def test_integer_units_equivalence_and_scale_identity(self):
        g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml');d={30:2}
        for scale in (1,2,256):
            for budget in (1,4,20):
                self.assertEqual(ScaledPressureSketch(g,{n:v*scale for n,v in d.items()},g.sha256,256,budget,scale).search(10,{50,60}),FrozenPressureSketch(g,d,g.sha256,256,budget).search(10,{50,60}))
        self.assertNotEqual(ScaledPressureSketch(g,{30:1},g.sha256,scale=1).context_sha256,ScaledPressureSketch(g,{30:1},g.sha256,scale=256).context_sha256)
        for scale in (0,-1,True):
            with self.assertRaises(ValueError):ScaledPressureSketch(g,{},g.sha256,scale=scale)
    def test_zero_alpha_identity_budget_and_context(self):
        g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml');d={30:2};engine=ScaledPressureSketch(g,d,g.sha256,256,20);identity=engine.context_sha256;result=engine.search(10,{50,60});d[30]=99
        self.assertEqual(engine.search(10,{50,60}),result);self.assertEqual(engine.context_sha256,identity)
        self.assertNotEqual(ScaledPressureSketch(g,d,g.sha256,256,20).context_sha256,identity)
        for budget in range(1,9):self.assertEqual(ScaledPressureSketch(g,d,g.sha256,0,budget).search(10,{50,60}),Sketch(g,'rr_length_switch',budget).search(10,{50,60}))
        for bad in ({30:-1},{'30':1},{999:1},{30:True}):
            with self.assertRaises(ValueError):ScaledPressureSketch(g,bad,g.sha256)
        with self.assertRaises(ValueError):ScaledPressureSketch(g,{},'other')

if __name__=='__main__':unittest.main()
