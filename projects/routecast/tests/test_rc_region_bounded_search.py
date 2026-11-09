"""RC mathematical optimum certificate does not certify bounded search status."""
import unittest
from fractions import Fraction as F
from test_integer_rc_budget_boundaries import IntegerBudgetBoundaries
from native_integer_rc_search import NativeIntegerRC
from csr_integer_budget_search import query
from rc_feasible_cost_region import RCFeasibleCostRegion

class BoundedRegionTests(unittest.TestCase):
 def test_irrelevant_cost_change_can_exhaust_labels(self):
  rc,scaled,costs=IntegerBudgetBoundaries().graph([(0,3,10,F(1,7)),(0,1,1,F(1,7)),(1,2,1,F(1,7))])
  scaled.fields['costs']=costs;scaled.fields['capacities']=[1]*4
  f=scaled.fields;budget=scaled.scale
  region=RCFeasibleCostRegion(4,[(u,f['dest_ranks'][i],scaled.increments[i],costs[i]) for u in range(4) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])])
  footprint=region.destinations(0,3,scaled.initial(0),budget)
  self.assertEqual(footprint,frozenset({3}))
  self.assertEqual(region.prefix_destinations(0,scaled.initial(0),budget),frozenset({1,2,3}))
  native=NativeIntegerRC(scaled);results=[]
  for demand in ({1:20},{}):
   native.set_other(demand)
   result=native.query(0,3,budget,3)
   expected=query(scaled,0,3,budget,lambda u,i:True,lambda u,i:costs[i]*(1+demand.get(f['dest_ranks'][i],0)),3)
   self.assertEqual(result,expected);results.append(result)
   # Removing the resource cap confirms the mathematical optimum is unchanged.
   unlimited=native.query(0,3,budget,100)
   self.assertEqual(unlimited['status'],'FOUND');self.assertEqual(unlimited['cost'],10);self.assertEqual(unlimited['physical_edge_ids'],[0])
  self.assertEqual([r['status'] for r in results],['FOUND','LABEL_LIMIT'])
if __name__=='__main__':unittest.main()
