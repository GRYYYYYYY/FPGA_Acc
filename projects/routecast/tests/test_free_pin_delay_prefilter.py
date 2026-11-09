import random
import unittest
from test_budget_pin_candidates import BudgetPinTests
from prepared_budget_pin_candidates import PreparedBudgetPins
from free_pin_delay_prefilter import feasible_targets

class DelayPrefilterTests(unittest.TestCase):
    def test_random_feasibility_matches_exact_query(self):
        graph = BudgetPinTests().fixture()
        engine = PreparedBudgetPins(graph)
        rng = random.Random(20261005)
        for _ in range(300):
            n = len(graph.edges)
            costs = [rng.randrange(8) for _ in range(n)]
            delays = [rng.randrange(8) for _ in range(n)]
            blocked = {3} if rng.randrange(5) == 0 else set()
            forbidden = {e for e in range(n) if rng.randrange(6) == 0}
            budget = rng.randrange(40)
            context = engine.prepare(costs, delays, blocked)
            result = feasible_targets(engine, context, 0, 6, 0, [0, 1], budget, forbidden)
            for ptc in [0, 1]:
                query = engine.query_prepared(context, 0, 6, 0, ptc, budget, blocked_edges=forbidden, max_labels=100000)
                self.assertNotEqual(query['status'], 'LABEL_LIMIT')
                self.assertEqual(ptc in result['feasible_targets'], query['status'] == 'FOUND')
                minimum = engine.query_prepared(context, 0, 6, 0, ptc, budget,
                    cost_overrides=dict(enumerate(delays)), blocked_edges=forbidden)
                if minimum['status'] == 'FOUND':
                    self.assertEqual(result['minimum_delays'][ptc], minimum['delay'])

    def test_subsets_empty_and_invalid_inputs(self):
        from dataclasses import replace
        graph = BudgetPinTests().fixture()
        engine = PreparedBudgetPins(graph)
        n = len(graph.edges)
        context = engine.prepare([0]*n, [0]*n)
        for targets in ([], [0], [1], [1, 0, 1]):
            result = feasible_targets(engine, context, 0, 6, 0, targets, 0)
            self.assertEqual(result['feasible_targets'], sorted(set(targets)))
        base = dict(engine=engine, context=context, source=0, sink=6,
                    source_ptc=0, targets=[0, 1], budget=0)
        for extra in ({'context':replace(context)}, {'source':True},
                      {'sink':True}, {'source_ptc':True}, {'budget':True},
                      {'budget':-1}, {'targets':[True]}, {'targets':[999]},
                      {'blocked_edges':[True]}, {'blocked_edges':[n]}):
            args = dict(base); args.update(extra)
            with self.assertRaises(ValueError):
                feasible_targets(**args)
