import random
import unittest
from fractions import Fraction as F

from csr_exact_buffered_rc import ExactBufferedRC
from csr_exact_budget_search import query as fractional
from csr_integer_budget_search import query as integer
from integer_rc_context import IntegerRC


class IntegerBudgetBoundaries(unittest.TestCase):
    def graph(self, edges, count=4):
        rows, dest, ids, switches, costs = [0], [], [], {}, []
        for node in range(count):
            for eid, (u, v, cost, delay) in enumerate(edges):
                if u == node:
                    dest.append(v)
                    ids.append(eid)
                    costs.append(cost)
                    switches[eid] = (F(0), delay)
            rows.append(len(ids))
        fields = dict(node_ids=list(range(count)), row_offsets=rows,
                      dest_ranks=dest, edge_ids=ids, switch_ids=ids)
        rc = ExactBufferedRC(fields, [0]*count, [(F(2, 3), F(1, 5))], switches)
        return rc, IntegerRC(rc), costs

    def compare(self, rc, scaled, costs, budget, limit=1000, blocked=()):
        allowed = lambda n, i: i not in blocked
        objective = lambda n, i: costs[i]
        a = fractional(rc, 0, len(rc.fields['node_ids'])-1, budget,
                       allowed, objective, limit)
        b = integer(scaled, 0, len(rc.fields['node_ids'])-1,
                    scaled.encode(budget), allowed, objective, limit)
        converted = dict(b)
        if b['delay'] is not None:
            converted['delay'] = F(b['delay'], scaled.scale)
        self.assertEqual(a, converted)
        if a['status'] != 'FOUND':
            self.assertIsNone(a['physical_edge_ids'])
            self.assertIsNone(a['cost'])
            self.assertIsNone(a['delay'])
        return a

    def test_limits_budget_and_eligibility(self):
        rc, scaled, costs = self.graph([
            (0, 1, 3, F(1, 7)), (0, 2, 0, F(1, 3)),
            (1, 3, 3, F(1, 7)), (2, 3, 0, F(1, 3))])
        budget = rc.path(0, 3, [0, 2])
        self.assertEqual(self.compare(rc, scaled, costs, budget)['physical_edge_ids'], [0, 2])
        self.assertEqual(self.compare(rc, scaled, costs, budget-F(1, scaled.scale))['status'], 'UNREACHABLE')
        self.assertEqual(self.compare(rc, scaled, costs, budget, limit=1)['status'], 'LABEL_LIMIT')
        self.assertEqual(self.compare(rc, scaled, costs, budget, blocked=(0, 1))['status'], 'UNREACHABLE')
        self.assertEqual(self.compare(rc, scaled, costs, F(0))['labels_created'], 0)

    def test_exhaustive_rational_dags(self):
        rng = random.Random(20261006)
        for case in range(80):
            edges = [(u, v, rng.randrange(5), F(rng.randrange(5), rng.choice([7, 11, 13])))
                     for u in range(5) for v in range(u+1, 6) if rng.random() < .6]
            rc, scaled, costs = self.graph(edges, 6)
            budget = F(rng.randrange(2*scaled.scale), scaled.scale)
            result = self.compare(rc, scaled, costs, budget)
            feasible = []
            def visit(node, objective, delay):
                if delay > budget:
                    return
                if node == 5:
                    feasible.append((objective, delay))
                    return
                for slot in range(rc.fields['row_offsets'][node], rc.fields['row_offsets'][node+1]):
                    visit(rc.fields['dest_ranks'][slot], objective+costs[slot], delay+rc.increment(slot))
            visit(0, 0, F(1, 15))
            if feasible:
                self.assertEqual((result['cost'], result['delay']), min(feasible))
            else:
                self.assertEqual(result['status'], 'UNREACHABLE')

    def test_invalid_integer_contract_and_off_lattice_budget(self):
        rc, scaled, costs = self.graph([(0, 3, 1, F(1, 7))])
        for budget in (True, -1, F(1), 1.0):
            with self.assertRaises(ValueError):
                integer(scaled, 0, 3, budget, lambda n, i: True, lambda n, i: 0)
        with self.assertRaises(ValueError):
            scaled.encode(F(1, scaled.scale*2))
        with self.assertRaises(ValueError):
            integer(scaled, 0, 3, scaled.scale, lambda n, i: True, lambda n, i: -1)


if __name__ == '__main__':
    unittest.main()
