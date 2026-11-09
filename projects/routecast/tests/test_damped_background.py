from pathlib import Path
import sys,unittest,random
from fractions import Fraction
from math import ceil
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from damped_background import half_background
from rr_graph import read_rr_graph
from frozen_pressure_sketch import FrozenPressureSketch

class DampingTests(unittest.TestCase):
    def setUp(self):self.g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml')
    def test_integer_average_against_fraction_and_no_alias(self):
        rng=random.Random(20261007)
        for _ in range(100):
            a={n:rng.randrange(50) for n in self.g.nodes};b={n:rng.randrange(50) for n in self.g.nodes};before=(dict(a),dict(b));r=half_background(self.g,a,b)
            expected={n:ceil(Fraction(a[n]+b[n],2)) for n in a}
            self.assertEqual(r,{n:v for n,v in expected.items() if v});self.assertEqual((a,b),before);r.clear();self.assertEqual((a,b),before)
    def test_q8_first_two_updates_have_no_demand_rounding(self):
        rng=random.Random(20261008)
        for _ in range(100):
            initial=rng.randrange(20);state={30:initial*256};exact=Fraction(initial)
            for update in range(2):
                observed=rng.randrange(20);state=half_background(self.g,state,{30:observed*256});exact=(exact+observed)/2
                self.assertEqual(Fraction(state.get(30,0),256),exact)
        state={30:256}
        for _ in range(2):state=half_background(self.g,state,{})
        self.assertEqual(state,{30:64})

    def test_sparse_sticky_unit_validation_and_cost_context(self):
        a={30:2};b={30:0};r=half_background(self.g,a,b);self.assertEqual(r,{30:1});self.assertEqual(half_background(self.g,r,{}),r)
        old=FrozenPressureSketch(self.g,a,self.g.sha256);new=FrozenPressureSketch(self.g,r,self.g.sha256);self.assertNotEqual(old.context_sha256,new.context_sha256)
        for values in ({30:-1},{'30':1},{30:True},{999:1},None):
            with self.assertRaises(ValueError):half_background(self.g,values,{})
        self.assertEqual(half_background(self.g,{},{}),{})

if __name__=='__main__':unittest.main()
