import itertools,random,unittest
from costed_pin_assignment import assign_costed
class CostedTests(unittest.TestCase):
 def test_reassignment_beats_greedy(self):
  c={0:{(1,0):0,(1,1):2},1:{(1,0):1,(1,1):100}}
  r=assign_costed(c);self.assertEqual(r['total_cost'],3)
  self.assertEqual(r,assign_costed(dict(reversed(list(c.items())))))
 def test_random_exhaustive(self):
  rng=random.Random(20261005)
  for _ in range(300):
   c={r:{(0,p):rng.randrange(20) for p in range(5) if rng.random()<.55} for r in range(rng.randrange(6))}
   totals=[sum(c[r][p] for r,p in zip(c,choice)) for choice in itertools.product(*(list(v) for v in c.values())) if len(set(choice))==len(choice)]
   result=assign_costed(c)
   if totals:self.assertEqual(result['total_cost'],min(totals));self.assertEqual(result['status'],'matched')
   else:self.assertEqual(result['status'],'infeasible');self.assertEqual(result['assignment'],{})
 def test_invalid_cost(self):
  for cost in (-1,True,1.5):
   with self.assertRaises(ValueError):assign_costed({0:{(0,0):cost}})
