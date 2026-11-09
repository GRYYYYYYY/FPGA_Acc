import random
import unittest
from potential_occupancy_threshold import required_other_demand


class ThresholdTests(unittest.TestCase):
    def test_exhaustive_demand_equivalence(self):
        rng = random.Random(20261006)
        for case in range(500):
            destination = rng.randrange(500)
            incoming = [(rng.randrange(500), rng.randrange(1, 80))
                        for _ in range(rng.randrange(15))]
            threshold = required_other_demand(destination, incoming)
            for demand in range(510):
                self.assertEqual(demand >= threshold,
                                 all(destination <= source+scalar*(1+demand)
                                     for source, scalar in incoming))

    def test_exact_integer_boundary_and_invalid(self):
        self.assertEqual(required_other_demand(10, [(0, 3)]), 3)
        self.assertEqual(required_other_demand(9, [(0, 3)]), 2)
        self.assertEqual(required_other_demand(0, []), 0)
        huge = 1 << 140
        self.assertEqual(required_other_demand(huge+1, [(0, huge)]), 1)
        for incoming in ([(0, 0)], [(True, 3)], [(0, 1.0)], [(-1, 3)]):
            with self.assertRaises(ValueError):
                required_other_demand(10, incoming)

if __name__ == '__main__':
    unittest.main()
