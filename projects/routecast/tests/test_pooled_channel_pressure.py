import unittest
from fractions import Fraction
from pooled_channel_pressure import rows


class PoolTests(unittest.TestCase):
    def fixture(self):
        return {'types': [4, 4, 4, 1], 'directions': [1, 1, 2, 0],
                'segments': [0] * 4, 'xlow': [0] * 4, 'xhigh': [1] * 4,
                'ylow': [0] * 4, 'yhigh': [0] * 4, 'layer': [0] * 4,
                'capacities': [1, 3, 1, 1]}

    def test_capacity_weighted_excess_conserved_without_pooling_directions(self):
        fields = self.fixture()
        pressure, proof = rows(fields, {0: 3, 1: 0, 2: 2, 3: 100})
        self.assertEqual(pressure[0][1], Fraction(3, 2))
        self.assertEqual(pressure[1][1], Fraction(3, 2))
        self.assertEqual(pressure[2][1], 2)
        self.assertNotIn(3, pressure)
        self.assertEqual(sum(cap * (value - 1) for cap, value in pressure.values()), 3)
        self.assertEqual(len(proof), 2)

    def test_invalid_occupancy_rejected_and_no_overuse_produces_empty_rows(self):
        self.assertEqual(rows(self.fixture(), {})[0], {})
        with self.assertRaises(ValueError):
            rows(self.fixture(), {0: -1})


if __name__ == '__main__':
    unittest.main()
