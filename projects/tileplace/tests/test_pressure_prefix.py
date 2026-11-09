"""Compare indexed pressure with an independent unit-edge walk."""

import itertools
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
from tileplace_v2 import TilePlaceV2Engine, PRESSURE_ONE


def walk(values, a, b, horizontal_first):
    x, y = a
    total = 0
    for axis in ((0, 1) if horizontal_first else (1, 0)):
        while (x if axis == 0 else y) != b[axis]:
            before = (x, y)
            step = 1 if b[axis] > before[axis] else -1
            x, y = (x + step, y) if axis == 0 else (x, y + step)
            first, second = sorted((before, (x, y)))
            total += PRESSURE_ONE + values.get((*first, *second), 0)
    return total


class PressurePrefixTests(unittest.TestCase):
    def test_invalid_refresh_leaves_pressure_and_indexes_unchanged(self):
        engine = object.__new__(TilePlaceV2Engine)
        engine._net_cost_cache = {}
        engine.pressure_q16 = {(0, 0, 1, 0): 7}
        before = engine._path_pressure((0, 0), (1, 0), True)
        with self.assertRaises(ValueError):
            engine.pressure_q16 = {(0, 0): 99}
        self.assertEqual(dict(engine.pressure_q16), {(0, 0, 1, 0): 7})
        self.assertEqual(engine._path_pressure((0, 0), (1, 0), True), before)

    def test_sparse_negative_coordinates_all_directions_and_refresh(self):
        randomizer = random.Random(10856)
        engine = object.__new__(TilePlaceV2Engine)
        points = list(itertools.product(range(-3, 4), repeat=2))
        for refresh in range(2):
            values = {}
            for x, y in points:
                for key in ((x, y, x + 1, y), (x, y, x, y + 1)):
                    if randomizer.randrange(3) == 0:
                        values[key] = randomizer.randrange(1 << 70)
            engine._net_cost_cache = {1: (1, 2, 3)}
            engine.pressure_q16 = values
            self.assertEqual(engine._net_cost_cache, {})
            for a, b in itertools.product(points, repeat=2):
                for order in (False, True):
                    self.assertEqual(engine._path_pressure(a, b, order), walk(values, a, b, order))
            with self.assertRaises(TypeError):
                engine.pressure_q16[(0, 0, 1, 0)] = 1
        engine.pressure_q16 = {}
        self.assertEqual(engine._path_pressure((-10, 3), (100, -8), True), 121 * PRESSURE_ONE)


if __name__ == "__main__":
    unittest.main()
