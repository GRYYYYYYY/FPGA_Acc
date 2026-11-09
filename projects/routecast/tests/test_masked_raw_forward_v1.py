import sys,unittest,random,heapq
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from masked_raw_forward_v1 import Search
B=Path(__file__).resolve().parents[1]/'experiments/wide_cost_backend_build_v1_2026-10-13/search.so'
class Contract(unittest.TestCase):
 def test_random_masked_searches_and_restoration(self):
  rng=random.Random(812);count=0
  for trial in range(40):
   n=rng.randrange(3,10);rows=[0];dest=[];cost=[]
   for u in range(n):
    for v in range(n):
     if u!=v and rng.randrange(4)==0:dest.append(v);cost.append(rng.randrange(5)+(1<<66 if trial%3==0 else 0))
    rows.append(len(dest))
   f={'row_offsets':rows,'dest_ranks':dest,'capacities':[1]*n};rc=SimpleNamespace(increments=cost,initial=lambda u:7);s=Search(f,rc,B)
   try:
    for turn in range(4):
     source=0;targets={n-1};blocked={v for v in range(1,n-1) if turn%2 and rng.randrange(3)==0};answer=s.query(source,targets,blocked)['answers'][n-1]
     d={0:7};q=[(7,0)]
     while q:
      val,u=heapq.heappop(q)
      if val!=d[u]:continue
      for i in range(rows[u],rows[u+1]):
       v=dest[i];new=val+cost[i]
       if v not in blocked and (v not in d or new<d[v]):d[v]=new;heapq.heappush(q,(new,v))
     self.assertEqual(answer['reachable'],n-1 in d)
     if n-1 in d:
      self.assertEqual(answer['minimum'],d[n-1]);self.assertEqual(7+sum(cost[i] for i in answer['slots']),d[n-1])
     self.assertEqual(tuple(s.engine.cap),tuple(f['capacities']));count+=1
   finally:s.close()
  self.assertEqual(count,160)
 def test_rejections_and_backend_failure_restore(self):
  s=Search({'row_offsets':[0,1,2,2],'dest_ranks':[1,2],'capacities':[1]*3},SimpleNamespace(increments=[1,1],initial=lambda n:0),B)
  with self.assertRaises(ValueError):s.query(0,[2],[0])
  original=s.engine.search
  def fail(*args):raise RuntimeError('injected')
  s.engine.search=fail
  with self.assertRaises(RuntimeError):s.query(0,[2],[1])
  self.assertEqual(tuple(s.engine.cap),(1,1,1));s.engine.search=original;s.close()
if __name__=='__main__':unittest.main()
