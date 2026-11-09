from pathlib import Path
import sys,unittest
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from native_indexed_cost import parse_cost_echo,NativeBaseSketch
from rr_graph import read_rr_graph
TEXT='''Delay normalization factor: 1
Cost Index Base Cost Ortho Cost Index Seg Index Inv. Length T. Linear T. Quadratic C. Load
0 SOURCE 1 -1 -1 nan 0 0 0
1 SINK 0 -1 -1 nan 0 0 0
2 OPIN 1 -1 -1 nan 0 0 0
3 IPIN 0.95 -1 -1 nan 0 0 0
4 CHANX test 4 5 0 0.25 0 0 0
5 CHANY test 4 4 0 0.25 0 0 0
'''
class NativeCostTests(unittest.TestCase):
    def graph(self):
        g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml');nodes={n:replace(v,segment_id=0 if v.type in {'CHANX','CHANY'} else v.segment_id) for n,v in g.nodes.items()};return replace(g,nodes=nodes,segments={0:'<segment id="0" name="test"/>'})
    def test_exact_normalization_mapping_and_zero_sink_cost(self):
        g=self.graph();engine=NativeBaseSketch(g,TEXT,g.sha256,100);self.assertEqual(engine.node_costs[30],400);self.assertEqual(engine.node_costs[40],95);self.assertEqual(engine.node_costs[50],0);self.assertEqual(engine.search(10,{50,60}).paths,{50:(0,1,2,3),60:(0,1,2,4)})
        for source,arcs in engine.outgoing.items():
            for eid,dst,cost in arcs:self.assertEqual(cost,engine.node_costs[dst])
    def test_reject_ambiguous_unsupported_corrupt_echo(self):
        for bad in (TEXT.replace('factor: 1','factor: nan'),TEXT.replace('0.95','-0.95'),TEXT+TEXT.splitlines()[-1]+'\n',TEXT.replace('CHANX test','CHANX other'),TEXT.replace('4 5 0 0.25','4 4 0 0.25')):
            with self.assertRaises(ValueError):parse_cost_echo(bad)
        g=self.graph()
        with self.assertRaises(ValueError):NativeBaseSketch(g,TEXT,'other')
        with self.assertRaises(ValueError):NativeBaseSketch(replace(g,segments={0:'<segment name="other"/>'}),TEXT,g.sha256)
        with self.assertRaises(ValueError):NativeBaseSketch(g,TEXT,g.sha256,True)
if __name__=='__main__':unittest.main()
