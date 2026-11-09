"""Differential queries against the sealed Python reference implementation."""
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "tools"))
from tileplace_v2 import TilePlaceV2Engine


class PressureTest(unittest.TestCase):
    def test_python_equivalence(self):
        rng = random.Random(29092026)
        edges = {}
        for _ in range(600):
            x, y = rng.randrange(-20, 21), rng.randrange(-20, 21)
            dx, dy = rng.choice([(1, 0), (0, 1), (-1, 0), (2, 0)])
            edges[x, y, x+dx, y+dy] = rng.randrange(1 << 35)
        queries = [(rng.randrange(-30, 31), rng.randrange(-30, 31),
                    rng.randrange(-30, 31), rng.randrange(-30, 31)) for _ in range(2000)]
        queries += [(0, 0, 0, 0), (-20, -20, 20, 20), (20, 20, -20, -20)]
        reference = TilePlaceV2Engine.__new__(TilePlaceV2Engine)
        reference.pressure_q16 = edges
        payload = [f"{len(edges)} {len(queries)}"]
        payload += [" ".join(map(str, (*edge, weight))) for edge, weight in edges.items()]
        payload += [" ".join(map(str, query)) for query in queries]
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "query"
            subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-O2",
                            str(ROOT / "pressure_query.cpp"), "-o", str(binary)], check=True)
            result = subprocess.run([str(binary)], input="\n".join(payload)+"\n",
                                    text=True, capture_output=True, check=True)
        actual = [tuple(map(int, line.split())) for line in result.stdout.splitlines()]
        expected = []
        for x, y, bx, by in queries:
            h = reference._path_pressure((x, y), (bx, by), True)
            v = reference._path_pressure((x, y), (bx, by), False)
            expected.append((h, v, min(h, v)))
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
