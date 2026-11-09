from pathlib import Path
import sys, unittest, random
from fractions import Fraction as F
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rr_graph import read_rr_graph
from path_rc import PathRC, State

class PathRCTests(unittest.TestCase):
    def graph(self, kind='pass_gate', internal='0'):
        g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml')
        nodes={n:replace(v,timing=(('R','4'),('C','3'))) for n,v in g.nodes.items()}
        return replace(g,nodes=nodes,switches={5:f'<switch id="5" type="{kind}"><timing R="2" Tdel="7" Cinternal="{internal}"/></switch>'})
    def test_pass_gate_accumulates_and_buffer_resets(self):
        self.assertEqual(PathRC(self.graph()).path(10,(0,1)),State(F(12),F(56)))
        for kind in ('mux','tristate','buffer'):
            self.assertEqual(PathRC(self.graph(kind)).path(10,(0,1),99),State(F(6),F(38)))
        self.assertEqual(PathRC(self.graph('short')).path(10,(0,1)),State(F(12),F(56)))
    def test_internal_cap_and_explicit_tree_start(self):
        self.assertEqual(PathRC(self.graph(internal='5')).path(10,(0,),10,11),State(F(16),F(130)))
        # VPR correction can be signed; never clip it or assume Dijkstra weights.
        g=self.graph('buffer','5');nodes=dict(g.nodes);nodes[10]=replace(nodes[10],timing=(('R','100'),('C','0')))
        self.assertEqual(PathRC(replace(g,nodes=nodes)).path(10,(0,)).delay,F(-201))
    def test_random_against_expanded_polynomial(self):
        rng=random.Random(20261004)
        for _ in range(100):
            r,c,sr,t,ci,up=[F(rng.randrange(20)) for _ in range(6)]
            kind=rng.choice(['mux','pass_gate']);g=self.graph(kind);nodes={n:replace(v,timing=(('R',str(r)),('C',str(c)))) for n,v in g.nodes.items()}
            sw={5:f'<switch id="5" type="{kind}"><timing R="{sr}" Tdel="{t}" Cinternal="{ci}"/></switch>'}
            state=PathRC(replace(g,nodes=nodes,switches=sw)).step(State(up,F(0)),0)
            retained=up if kind=='pass_gate' else F(0)
            self.assertEqual(state.delay,t+retained*(c+ci)+sr*(c+ci)+r*c/2+r*ci/2)
    def test_validation(self):
        model=PathRC(self.graph())
        for path in ((1,), (0,3), (-1,), (True,)):
            with self.assertRaises(ValueError):model.path(10,path)
        for bad in ('nan','inf','-1'):
            with self.assertRaises(ValueError):PathRC(self.graph(internal=bad))
        g=self.graph();nodes=dict(g.nodes);nodes[10]=replace(nodes[10],timing=())
        with self.assertRaises(ValueError):PathRC(replace(g,nodes=nodes))
        with self.assertRaises(ValueError):PathRC(self.graph('unknown'))

if __name__=='__main__':unittest.main()
