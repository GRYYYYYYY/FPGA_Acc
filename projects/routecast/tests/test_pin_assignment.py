import itertools,random,unittest
from pin_assignment import assign
class MatchingTests(unittest.TestCase):
 def test_augmenting_reassignment_and_determinism(self):
  a={0:[(1,0),(1,1)],1:[(1,0)]};r=assign(a);self.assertEqual(r['assignment'],{0:[1,1],1:[1,0]});self.assertEqual(assign(dict(reversed(list(a.items())))),r)
 def test_hall_overlap_failure_has_no_partial_assignment(self):
  a={0:[(1,0)],1:[(1,0)],2:[(1,1),(1,2)]};r=assign(a);self.assertEqual(r['status'],'infeasible');self.assertEqual(r['assignment'],{});self.assertEqual(r['hall_witness']['request_ids'],[0,1]);self.assertEqual(r['hall_witness']['deficiency'],1)
 def test_random_small_graphs_against_exhaustive_oracle(self):
  rng=random.Random(72491)
  for _ in range(250):
   n=rng.randrange(1,6);pins=[(1,i) for i in range(rng.randrange(1,6))];a={r:[p for p in pins if rng.random()<.5] for r in range(n)};saved={r:list(v) for r,v in a.items()};r=assign(a);possible=any(len(set(combo))==n for combo in itertools.product(*(a[i] for i in range(n))))
   self.assertEqual(r['status']=='matched',possible);self.assertEqual(a,saved)
   if possible:
    values=[tuple(v) for v in r['assignment'].values()];self.assertEqual(len(set(values)),n);self.assertTrue(all(tuple(v) in a[k] for k,v in r['assignment'].items()))
   else:
    w=r['hall_witness'];neighbors={p for k in w['request_ids'] for p in a[k]};self.assertEqual(neighbors,{tuple(p) for p in w['physical_pins']});self.assertLess(len(neighbors),len(w['request_ids']))
 def test_empty_and_invalid(self):
  self.assertEqual(assign({})['assignment'],{})
  for a in ({True:[(1,0)]},{0:[(True,0)]},{0:[(1,0),(1,0)]}):
   with self.assertRaises(ValueError):assign(a)
if __name__=='__main__':unittest.main()
