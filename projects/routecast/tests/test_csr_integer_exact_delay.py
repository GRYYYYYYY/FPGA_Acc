import unittest,random
from fractions import Fraction as F
from csr_exact_buffered_rc import ExactBufferedRC
from csr_min_delay_feasibility import query as reference
from csr_integer_exact_delay import IntegerRC,query
class Test(unittest.TestCase):
 def test_fractional_parity(self):
  rng=random.Random(121)
  for case in range(50):
   edges=[(a,b,F(rng.randrange(5),rng.choice([3,7,10]))) for a in range(6) for b in range(6) if a!=b and rng.random()<.25];rows=[0];dst=[];ids=[];switches={0:(F(0),F(0))}
   for a in range(6):
    for j,(u,v,d) in enumerate(edges):
     if u==a:dst.append(v);ids.append(j);switches[j]=(F(0),d)
    rows.append(len(ids))
   rc=ExactBufferedRC({'node_ids':list(range(6)),'row_offsets':rows,'edge_ids':ids,'dest_ranks':dst,'switch_ids':ids},[0]*6,[(F(2,3),F(1,7))],switches);integer=IntegerRC(rc);allowed=lambda n,i:i%4!=2
   for cap in [1,100]:
    budget=F(rng.randrange(20),11);a=reference(rc,0,5,budget,allowed,max_labels=cap);b=query(integer,0,5,budget,allowed,max_nodes=cap)
    for key in b:self.assertEqual(a[key],b[key])
if __name__=='__main__':unittest.main()
