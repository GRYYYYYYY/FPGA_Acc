import unittest
from fractions import Fraction as F
from csr_exact_buffered_rc import ExactBufferedRC
from csr_reverse_delay_bound import incoming,prepare
from csr_exact_budget_search import query as plain
from csr_exact_budget_search_pruned import query
class Test(unittest.TestCase):
 def test_partial_bound_and_search_parity(self):
  import random
  rng=random.Random(83)
  for case in range(50):
   edges=[(a,b,rng.randrange(4),rng.randrange(4)) for a in range(6) for b in range(6) if a!=b and rng.random()<.25]
   rows=[0];dst=[];eid=[];sids=[];cost=[];switches={0:(F(0),F(0))}
   for a in range(6):
    for j,(u,v,w,d) in enumerate(edges):
     if u==a:dst.append(v);eid.append(j);sids.append(j);cost.append(w);switches[j]=(F(0),F(d))
    rows.append(len(eid))
   rc=ExactBufferedRC({'node_ids':list(range(6)),'row_offsets':rows,'edge_ids':eid,'dest_ranks':dst,'switch_ids':sids},[0]*6,[(F(0),F(0))],switches)
   allowed=lambda n,i:i%3!=1;reverse=incoming(rc.fields);full=prepare(rc,reverse,5,allowed,100);budget=F(rng.randrange(9));baseline=plain(rc,0,5,budget,allowed,lambda n,i:cost[i])
   for cap in (1,2,100):
    lower=prepare(rc,reverse,5,allowed,cap)
    for n in range(6):
     exact=full(n);bound=lower(n)
     if exact is not None:self.assertIsNotNone(bound);self.assertLessEqual(bound,exact)
    result=query(rc,0,5,budget,allowed,lambda n,i:cost[i],lower=lower)
    self.assertEqual((result['status'],result['cost'],result['delay']),(baseline['status'],baseline['cost'],baseline['delay']))
if __name__=='__main__':unittest.main()
