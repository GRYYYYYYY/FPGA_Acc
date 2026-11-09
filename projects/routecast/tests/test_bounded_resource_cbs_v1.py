import unittest
from tools.bounded_resource_cbs_v1 import search

class Branching(unittest.TestCase):
 def test_backtrack_and_new_conflict(self):
  options={0:[{1,2},{3}],1:[{1,3},{2,4}],2:[{4},{5}]}
  def tree(s):return {'support':set(s)}
  def route(n,mask):return next((tree(s) for s in options[n] if not mask.intersection(s)),None)
  def assess(trees):
   owners={}
   for n,t in trees.items():
    for r in t['support']:owners.setdefault(r,[]).append(n)
   for r,ns in sorted(owners.items()):
    if len(ns)>1:return [(n,r) for n in ns]
  out=search({n:route(n,set()) for n in options},assess,route,lambda ts:sum(len(t['support']) for t in ts.values()),100,100,5)
  self.assertEqual(out['status'],'FEASIBLE');self.assertIsNone(assess(out['trees']))
 def test_random_finite_domains_against_exhaustive(self):
  import random,itertools
  rng=random.Random(9127)
  for trial in range(100):
   options={n:[set(rng.sample(range(6),rng.randint(1,3))) for _ in range(3)] for n in range(3)}
   expected=any(len(set.union(*choice))==sum(map(len,choice)) for choice in itertools.product(*options.values()))
   def route(n,mask):return next(({'support':s} for s in options[n] if not s&mask),None)
   def assess(trees):
    for r in range(6):
     ns=[n for n,t in trees.items() if r in t['support']]
     if len(ns)>1:return [(n,r) for n in ns]
   answer=search({n:route(n,set()) for n in options},assess,route,lambda t:0,10000,10000,5)
   self.assertEqual(answer['status']=='FEASIBLE',expected,trial)
 def test_limit_is_not_unsat(self):
  out=search({0:{'support':{1}},1:{'support':{1}}},lambda t:[(0,1),(1,1)],lambda n,m:None,lambda t:0,max_states=0)
  self.assertEqual(out['status'],'LIMIT_REACHED')
 def test_exhaustion(self):
  out=search({0:{'support':{1}},1:{'support':{1}}},lambda t:[(0,1),(1,1)],lambda n,m:None,lambda t:0)
  self.assertEqual(out['status'],'EXHAUSTED_FIXED_DOMAIN')
if __name__=='__main__':unittest.main()
