import random
import unittest
from test_budget_pin_candidates import BudgetPinTests
from prepared_budget_pin_candidates import PreparedBudgetPins
from free_pin_budget_selection import choose

class PrefilterSelectionTests(unittest.TestCase):
    def test_random_exact_selection_and_limits(self):
        engine=PreparedBudgetPins(BudgetPinTests().fixture())
        rng=random.Random(20261015)
        for _ in range(300):
            n=len(engine.graph.edges)
            context=engine.prepare([rng.randrange(8) for _ in range(n)],
                                   [rng.randrange(8) for _ in range(n)],
                                   {3} if rng.randrange(5)==0 else set())
            kwargs=dict(blocked_edges={i for i in range(n) if rng.randrange(8)==0},
                        max_labels=rng.choice([1,5,100000]))
            args=(engine,context,0,6,0,0,rng.randrange(40),{0,1},{0})
            old=choose(*args,**kwargs)
            new=choose(*args,**kwargs,delay_prefilter=True)
            for field in ('status','best','targets','selection_complete','optimal_over_supplied_free_targets'):
                self.assertEqual(old[field],new[field])
            self.assertEqual([r['status'] for r in old['attempts']],
                             [r['status'] for r in new['attempts']])
    def test_invalid_options_even_if_all_targets_unreachable(self):
        engine=PreparedBudgetPins(BudgetPinTests().fixture());n=len(engine.graph.edges)
        context=engine.prepare([0]*n,[100]*n)
        for extra in ({'max_labels':True},{'cost_overrides':{0:True}},
                      {'delay_prefilter':1}):
            kwargs=dict(delay_prefilter=True);kwargs.update(extra)
            with self.assertRaises(ValueError):
                choose(engine,context,0,6,0,0,0,{0,1},{0},**kwargs)
