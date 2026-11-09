import random,unittest
from costed_pin_assignment import assign_costed
from pin_assignment_optimality import verify
class OptimalityTests(unittest.TestCase):
 def test_bad_swap_and_free_pin(self):
  c={0:{(0,0):5,(0,1):1},1:{(0,0):1,(0,1):5}}
  self.assertFalse(verify(c,{0:[0,0],1:[0,1]})['optimal'])
  self.assertFalse(verify({0:{(0,0):5,(0,1):1}},{0:[0,0]})['optimal'])
 def test_random_solver_optima(self):
  rng=random.Random(42)
  for _ in range(300):
   c={r:{(0,p):rng.randrange(30) for p in range(6) if rng.random()<.6} for r in range(rng.randrange(6))}
   result=assign_costed(c)
   if result['status']=='matched':self.assertTrue(verify(c,result['assignment'])['optimal'])
 def test_reject_bad_assignment(self):
  with self.assertRaises(ValueError):verify({0:{(0,0):0}},{0:[0,1]})
