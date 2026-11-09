import unittest,itertools,random
from tools.resumable_resource_cbs_v2 import search,restore_v1,SearchBudgetExceeded
class Resume(unittest.TestCase):
 def test_v1_recovers_unfinished_last_branch(self):
  root={n:{'support':{1}} for n in [0,1]};events=[{'state':0,'conflict':[[0,1],[1,1]]},{'state':1,'parent':0,'forbidden':[0,1],'pruned':True}]
  cp=restore_v1(root,events,lambda *x:None);self.assertEqual(cp['pending'],[{'state':0,'remaining':[(1,1)]}]);out=search(root,lambda t:None,lambda n,m:None,lambda t:0,checkpoint=cp);self.assertEqual(out['status'],'EXHAUSTED_FIXED_DOMAIN');self.assertEqual(out['queries'],1)
 def test_raw_budget_keeps_pending_branch(self):
  root={0:{'support':{1}},1:{'support':{1}}}
  def stop(n,m):raise SearchBudgetExceeded()
  first=search(root,lambda t:[(0,1),(1,1)],stop,lambda t:0);self.assertEqual(first['status'],'LIMIT_REACHED');self.assertEqual(first['queries'],0);self.assertEqual(len(first['checkpoint']['pending'][0]['remaining']),2)
  last=search(root,lambda t:None,lambda n,m:None,lambda t:0,checkpoint=first['checkpoint']);self.assertEqual(last['status'],'EXHAUSTED_FIXED_DOMAIN')
 def test_split_matches_brute_force(self):
  rng=random.Random(414)
  for _ in range(50):
   opts={n:[set(rng.sample(range(6),rng.randint(1,3))) for j in range(3)] for n in range(3)}
   def route(n,m):return next(({'support':s} for s in opts[n] if not s&m),None)
   def assess(t):
    for r in range(6):
     ns=[n for n,x in t.items() if r in x['support']]
     if len(ns)>1:return [(n,r) for n in ns]
   root={n:route(n,set()) for n in opts};expected=any(len(set.union(*s))==sum(map(len,s)) for s in itertools.product(*opts.values()));out=search(root,assess,route,lambda t:0,max_queries=1)
   for j in range(500):
    if out['status']!='LIMIT_REACHED':break
    out=search(root,assess,route,lambda t:0,max_queries=2,checkpoint=out['checkpoint'])
   self.assertNotEqual(out['status'],'LIMIT_REACHED');self.assertEqual(out['status']=='FEASIBLE',expected)
if __name__=='__main__':unittest.main()
