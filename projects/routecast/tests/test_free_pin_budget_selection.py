import unittest,random
from test_budget_pin_candidates import BudgetPinTests
from prepared_budget_pin_candidates import PreparedBudgetPins
from free_pin_budget_selection import choose
class FreePinTests(unittest.TestCase):
 def test_exhaustive_random_paths_and_occupied_targets(self):
  g=BudgetPinTests().fixture();e=PreparedBudgetPins(g);rng=random.Random(20261012)
  for _ in range(300):
   costs=[rng.randrange(8) for a in g.edges];delays=[rng.randrange(8) for a in g.edges];budget=rng.randrange(40);occupied={0,1} if rng.randrange(2) else {0};forbidden={i for i in range(len(g.edges)) if rng.randrange(8)==0};context=e.prepare(costs,delays);r=choose(e,context,0,6,0,0,budget,{0,1},occupied,blocked_edges=forbidden);answers=[]
   for ptc in {0}|({0,1}-occupied):
    targets=set(e.catalog.sinks[6].physical_pins[ptc]);opins=set(e.catalog.sources[0].physical_pins[0])
    def visit(node,seen,c,d):
     if d>budget:return
     if node==6:answers.append((c,d,ptc));return
     for eid in e.outgoing[node]:
      edge=g.edges[eid];dest=edge.sink
      if eid in forbidden or dest in seen or g.nodes[dest].capacity<=0:continue
      if node==0 and dest not in opins:continue
      if node in targets and dest!=6:continue
      if node!=0 and node not in targets and g.nodes[dest].type not in {'CHANX','CHANY'} and dest not in targets:continue
      visit(dest,seen|{dest},c+costs[eid],d+delays[eid])
    visit(0,{0},0,0)
   self.assertTrue(r['selection_complete'])
   if answers:self.assertEqual((r['best']['cost'],r['best']['delay'],r['best']['selected_ipin_ptc']),min(answers))
   else:self.assertEqual(r['status'],'UNREACHABLE')
 def test_limits_and_snapshot(self):
  e=PreparedBudgetPins(BudgetPinTests().fixture());n=len(e.graph.edges);context=e.prepare([0]*n,[0]*n);members={0,1};occupied={0}
  r=choose(e,context,0,6,0,0,0,members,occupied,max_labels=1);self.assertEqual(r['status'],'LABEL_LIMIT');self.assertFalse(r['selection_complete']);self.assertFalse(r['optimal_over_supplied_free_targets']);self.assertIsNone(r['best']);self.assertEqual(members,{0,1});self.assertEqual(occupied,{0})
  r=choose(e,context,0,6,0,0,0,{0},{0},equivalence='none');self.assertEqual(r['targets'],[0])
 def test_invalid_equivalence_and_pin_sets(self):
  e=PreparedBudgetPins(BudgetPinTests().fixture());n=len(e.graph.edges);context=e.prepare([0]*n,[0]*n)
  for members,occupied,equiv,current in [({0,1},{0},'none',0),({0,1},{True},'full',0),({0,99},{0},'full',0),({1},{0},'full',0),({0},{0},'unspecified',0),({0},{0},'full',True)]:
   with self.assertRaises(ValueError):choose(e,context,0,6,0,current,0,members,occupied,equivalence=equiv)
 def test_found_candidate_with_limited_competitor_is_not_optimal(self):
  e=PreparedBudgetPins(BudgetPinTests().fixture());n=len(e.graph.edges);context=e.prepare([0]*n,[0]*n);found=e.query_prepared(context,0,6,0,1,0);self.assertEqual(found['status'],'FOUND')
  class Partial:
   catalog=e.catalog
   def query_prepared(self,*args,**kwargs):return found if args[4]==1 else {'status':'LABEL_LIMIT','path':None,'cost':None,'delay':None}
  r=choose(Partial(),context,0,6,0,0,0,{0,1},{0});self.assertEqual(r['status'],'FOUND');self.assertEqual(r['best']['selected_ipin_ptc'],1);self.assertFalse(r['selection_complete']);self.assertFalse(r['optimal_over_supplied_free_targets'])
