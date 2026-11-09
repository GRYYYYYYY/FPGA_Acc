import unittest,sys,itertools,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from binary_owner_capacity_v1 import solve
class Contract(unittest.TestCase):
 def test_three_variable_formulas_against_exhaustive_assignments(self):
  rng=random.Random(234);pool=[((v,b),) for v in range(3) for b in [False,True]]+[((u,b),(v,c)) for u,v in itertools.combinations(range(3),2) for b in [False,True] for c in [False,True]]
  for trial in range(700):
   clauses=rng.sample(pool,rng.randrange(len(pool)+1));possible=[x for x in itertools.product([False,True],repeat=3) if all(not all(x[n]==b for n,b in c) for c in clauses)];r=solve(range(3),clauses);self.assertEqual(r['satisfiable'],bool(possible))
   if not r['satisfiable']:
    for key,start,end in [('false_to_true',False,True),('true_to_false',True,False)]:
     node=[r['conflict_NET'],start]
     for edge in r[key]:
      self.assertEqual(edge['from'],node);c=clauses[edge['clause']];arcs=[(list(c[0]),[c[-1][0],not c[-1][1]])]
      if len(c)==2:arcs.append((list(c[1]),[c[0][0],not c[0][1]]))
      self.assertIn((edge['from'],edge['to']),arcs);node=edge['to']
     self.assertEqual(node,[r['conflict_NET'],end])
 def test_empty_and_invalid(self):
  self.assertTrue(solve([],[])['satisfiable'])
  with self.assertRaises(ValueError):solve([0],[((1,True),)])
if __name__=='__main__':unittest.main()
