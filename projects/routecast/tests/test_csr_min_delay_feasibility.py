import unittest,random
from fractions import Fraction as F
from csr_exact_buffered_rc import ExactBufferedRC
from csr_min_delay_feasibility import query
class Test(unittest.TestCase):
 def test_exhaustive(self):
  rng=random.Random(19)
  for case in range(50):
   edges=[(a,b,rng.randrange(5)) for a in range(5) for b in range(a+1,6) if rng.random()<.5];rows=[0];dst=[];ids=[];switches={0:(F(0),F(0))}
   for a in range(6):
    for i,(u,v,d) in enumerate(edges):
     if u==a:dst.append(v);ids.append(i);switches[i]=(F(0),F(d))
    rows.append(len(ids))
   rc=ExactBufferedRC({'node_ids':list(range(6)),'row_offsets':rows,'edge_ids':ids,'dest_ranks':dst,'switch_ids':ids},[0]*6,[(F(0),F(0))],switches);budget=F(rng.randrange(10));feasible=[]
   def walk(n,d):
    if d>budget:return
    if n==5:feasible.append(d);return
    for i in range(rows[n],rows[n+1]):
     if i%3!=1:walk(dst[i],d+switches[ids[i]][1])
   walk(0,F(0));r=query(rc,0,5,budget,lambda n,i:i%3!=1)
   if feasible:self.assertEqual(r['status'],'FOUND');self.assertEqual(r['delay'],min(feasible))
   else:self.assertEqual(r['status'],'UNREACHABLE')
 def test_limit_is_not_unreachable(self):
  rc=ExactBufferedRC({'node_ids':[0,1],'row_offsets':[0,1,1],'edge_ids':[0],'dest_ranks':[1],'switch_ids':[0]},[0,0],[(F(0),F(0))],{0:(F(0),F(0))})
  self.assertEqual(query(rc,0,1,F(0),lambda n,i:True,max_labels=1)['status'],'NODE_LIMIT')
if __name__=='__main__':unittest.main()
