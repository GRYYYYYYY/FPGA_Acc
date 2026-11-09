import random,unittest
from dataclasses import replace
from test_budget_pin_candidates import BudgetPinTests
from budget_pin_candidates import BudgetPins
from prepared_budget_pin_candidates import PreparedBudgetPins,PreparedContext
class PreparedBudgetTests(unittest.TestCase):
 def test_complete_query_equivalence_and_snapshot(self):
  g=BudgetPinTests().fixture();old=BudgetPins(g);new=PreparedBudgetPins(g);rng=random.Random(20261009)
  for _ in range(300):
   costs=[rng.randrange(8) for e in g.edges];delays=[rng.randrange(8) for e in g.edges];blocked={3} if rng.randrange(5)==0 else set();context=new.prepare(costs,delays,blocked);overrides={e:rng.randrange(8) for e in range(len(costs)) if rng.randrange(4)==0};forbidden={e for e in range(len(costs)) if rng.randrange(6)==0};budget=rng.randrange(40);target=rng.randrange(2);limit=rng.choice([1,5,1000]);actual=[overrides.get(e,v) for e,v in enumerate(costs)]
   expected=old.query(0,6,0,target,actual,delays,budget,blocked,forbidden,max_labels=limit)
   costs[:]=[999]*len(costs);delays[:]=[999]*len(delays);blocked.clear()
   self.assertEqual(expected,new.query_prepared(context,0,6,0,target,budget,overrides,forbidden,max_labels=limit))
 def test_invalid_and_foreign_contexts(self):
  g=BudgetPinTests().fixture();e=PreparedBudgetPins(g);n=len(g.edges);c=e.prepare([0]*n,[0]*n)
  for bad in ([True]*n,[-1]*n,[0]*(n-1)):
   with self.assertRaises(ValueError):e.prepare(bad,[0]*n)
  with self.assertRaises(ValueError):e.prepare([0]*n,[0]*n,{0})
  foreign=PreparedBudgetPins(g).prepare([0]*n,[0]*n)
  for bad in (foreign,replace(c),PreparedContext(e,(),(),frozenset())):
   with self.assertRaises(ValueError):e.query_prepared(bad,0,6,0,0,0)
  for extra in ({'cost_overrides':{True:0}},{'cost_overrides':{0:True}},{'cost_overrides':{n:0}},{'blocked_edges':{True}},{'budget':True},{'target_ptc':True}):
   args=dict(context=c,source=0,sink=6,source_ptc=0,target_ptc=0,budget=0);args.update(extra)
   with self.assertRaises(ValueError):e.query_prepared(**args)
 def test_background_refresh_and_context_lifetime(self):
  import gc,weakref
  g=BudgetPinTests().fixture();e=PreparedBudgetPins(g);old=BudgetPins(g);n=len(g.edges);costs=[1]*n;delays=[1]*n
  open_context=e.prepare(costs,delays)
  closed_context=e.prepare(costs,delays,{3,8})
  for context,blocked in ((open_context,set()),(closed_context,{3,8}),(open_context,set())):
   self.assertEqual(old.query(0,6,0,0,costs,delays,100,blocked),e.query_prepared(context,0,6,0,0,100))
  disposable=e.prepare(costs,delays);identity=id(disposable);ref=weakref.ref(disposable);del disposable;gc.collect()
  self.assertIsNone(ref());self.assertNotIn(identity,e._contexts)
