import random
import unittest
from cost_read_dependency_index import CostReadDependencyIndex


class DependencyIndexTests(unittest.TestCase):
    def test_replacement_capture_and_context(self):
        index = CostReadDependencyIndex('graph-cost-budget-A')
        nodes = {1, 2}
        index.register('q', 'net', nodes)
        nodes.add(3)
        self.assertEqual(index.invalidate({3}), set())
        with self.assertRaises(ValueError):
            index.register('q', 'net', {-1})
        self.assertEqual(index.entries['q'][1], frozenset({1, 2}))
        index.register('q', 'net', {4})
        self.assertNotIn(1, index.readers)
        self.assertEqual(index.switch_context('graph-cost-budget-A'), set())
        self.assertEqual(index.switch_context('graph-cost-budget-B'), {'q'})
        self.assertEqual(dict(index.readers), {})

    def test_random_sequence_against_full_scan(self):
        rng = random.Random(20261006)
        index = CostReadDependencyIndex('fixed')
        reference = {}
        for step in range(500):
            if rng.random() < .7:
                q, owner = rng.randrange(40), rng.randrange(6)
                footprint = set(rng.sample(range(60), rng.randrange(12)))
                index.register(q, owner, footprint)
                reference[q] = (owner, footprint)
            else:
                dirty = set(rng.sample(range(60), rng.randrange(8)))
                excluded = rng.choice([None, 0, 1, 2, 3, 4, 5])
                expected = {q for q, (owner, footprint) in reference.items()
                            if dirty & footprint and (excluded is None or owner != excluded)}
                self.assertEqual(index.invalidate(dirty, excluded), expected)
                for q in expected:
                    del reference[q]
            self.assertEqual(index.entries, reference)
            reverse = {}
            for q, (_, footprint) in reference.items():
                for node in footprint:
                    reverse.setdefault(node, set()).add(q)
            self.assertEqual(dict(index.readers), reverse)

if __name__ == '__main__':
    unittest.main()
