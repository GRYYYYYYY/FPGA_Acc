import random,unittest
from fractions import Fraction as F
from test_integer_rc_budget_boundaries import IntegerBudgetBoundaries
from csr_integer_sink_bound_search import query
from csr_integer_budget_search import query as original
from rc_feasible_cost_region import RCFeasibleCostRegion
class BoundTests(unittest.TestCase):
 def test_dead_branch_label_limit_is_avoided(self):
  rc,integer,costs=IntegerBudgetBoundaries().graph([(0,3,10,F(1,7)),(0,1,1,F(1,7)),(1,2,1,F(1,7))]);f=integer.fields
  region=RCFeasibleCostRegion(4,[(u,f['dest_ranks'][i],integer.increments[i],costs[i]) for u in range(4) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])]);remaining=region.distance(3,True)
  plain=original(integer,0,3,integer.scale,lambda u,i:True,lambda u,i:costs[i],3);pruned=query(integer,0,3,integer.scale,lambda u,i:True,lambda u,i:costs[i],remaining,3)
  self.assertEqual(plain['status'],'LABEL_LIMIT');self.assertEqual(pruned['status'],'FOUND');self.assertEqual(pruned['physical_edge_ids'],[0]);self.assertEqual(pruned['cost'],10)
 def test_exact_optimum_matches_exhaustive_dags(self):
  rng=random.Random(2026100602)
  for _ in range(100):
   edges=[(u,v,rng.randrange(6),F(rng.randrange(4),7)) for u in range(5) for v in range(u+1,6) if rng.random()<.4];rc,integer,costs=IntegerBudgetBoundaries().graph(edges,6);f=integer.fields;budget=rng.randrange(2*integer.scale)
   region=RCFeasibleCostRegion(6,[(u,f['dest_ranks'][i],integer.increments[i],costs[i]) for u in range(6) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])]);remaining=region.distance(5,True);result=query(integer,0,5,budget,lambda u,i:True,lambda u,i:costs[i],remaining,1000);paths=[]
   def walk(u,delay,cost):
    if delay>budget:return
    if u==5:paths.append((cost,delay));return
    for i in range(f['row_offsets'][u],f['row_offsets'][u+1]):walk(f['dest_ranks'][i],delay+integer.increments[i],cost+costs[i])
   walk(0,integer.initial(0),0)
   if paths:self.assertEqual((result['cost'],result['delay']),min(paths))
   else:self.assertEqual(result['status'],'UNREACHABLE')
if __name__=='__main__':unittest.main()
