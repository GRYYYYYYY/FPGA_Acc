import unittest
from fractions import Fraction as F
from csr_exact_buffered_rc import ExactBufferedRC
from csr_exact_budget_search import query
class Test(unittest.TestCase):
 def engine(self):
  f={'node_ids':[0,1,2,3],'row_offsets':[0,2,3,4,4],'edge_ids':[0,1,2,3],'dest_ranks':[1,2,3,3],'switch_ids':[0,1,0,0]}
  return ExactBufferedRC(f,[0]*4,[(F(0),F(0))],{0:(F(0),F(1)),1:(F(0),F(3))})
 def test_budget_and_blocked_arc(self):
  rc=self.engine();costs=[3,0,3,0]
  run=lambda budget,allowed=lambda n,i:True,cap=100:query(rc,0,3,F(budget),allowed,lambda n,i:costs[i],cap)
  a=run(2);self.assertEqual((a['physical_edge_ids'],a['cost'],a['delay']),([0,2],6,F(2)))
  self.assertEqual(run(4)['physical_edge_ids'],[1,3]);self.assertEqual(run(1)['status'],'UNREACHABLE')
  self.assertEqual(run(4,lambda n,i:i!=1)['physical_edge_ids'],[0,2]);self.assertEqual(run(4,cap=1)['status'],'LABEL_LIMIT')
 def test_exhaustive_dag_parity(self):
  import random
  rng=random.Random(41)
  for case in range(50):
   edges=[(a,b,rng.randrange(5),rng.randrange(4)) for a in range(5) for b in range(a+1,6) if rng.random()<.5]
   rows=[0];dst=[];eid=[];switch=[];costs=[];switches={}
   for a in range(6):
    for j,(u,v,w,d) in enumerate(edges):
     if u==a:dst.append(v);eid.append(j);switch.append(j);costs.append(w);switches[j]=(F(0),F(d))
    rows.append(len(eid))
   if not switches:switches={0:(F(0),F(0))}
   rc=ExactBufferedRC({'node_ids':list(range(6)),'row_offsets':rows,'edge_ids':eid,'dest_ranks':dst,'switch_ids':switch},[0]*6,[(F(0),F(0))],switches)
   budget=F(rng.randrange(10));feasible=[]
   def visit(n,c,d):
    if d>budget:return
    if n==5:feasible.append((c,d));return
    for i in range(rows[n],rows[n+1]):visit(dst[i],c+costs[i],d+switches[switch[i]][1])
   visit(0,0,F(0));result=query(rc,0,5,budget,lambda n,i:True,lambda n,i:costs[i])
   if feasible:self.assertEqual((result['cost'],result['delay']),min(feasible))
   else:self.assertEqual(result['status'],'UNREACHABLE')
 def test_invalid(self):
  rc=self.engine()
  with self.assertRaises(ValueError):query(rc,0,3,4,lambda n,i:True,lambda n,i:0)
  with self.assertRaises(ValueError):query(rc,0,3,F(4),lambda n,i:True,lambda n,i:-1)
if __name__=='__main__':unittest.main()
