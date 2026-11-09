import unittest,sys,random
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from A_support_candidate_oracle_v1 import Oracle
B=Path(__file__).resolve().parents[1]/'experiments/wide_cost_backend_build_v1_2026-10-13/search.so'
def domain(n,edges):
 row=[0];dest=[];inc=[]
 for u in range(n):
  for a,b,c in edges:
   if a==u:dest.append(b);inc.append(c)
  row.append(len(dest))
 return {'row_offsets':row,'dest_ranks':dest,'capacities':[1]*n},SimpleNamespace(increments=inc,initial=lambda n:0)
class Contract(unittest.TestCase):
 def test_weighted_violation_cannot_prune_raw_feasible_tree(self):
  f,rc=domain(4,[(0,1,5),(1,3,5),(0,2,1),(2,3,1)]);o=Oracle(f,rc,B,{1,2},{1})
  try:
   out=o.query(0,{3:5},set());self.assertTrue(out['within_budget']);self.assertFalse(out['pruning_allowed']);self.assertEqual(out['kind'],'RAW_FEASIBLE_FALLBACK');self.assertEqual(out['answers'][3]['raw_cost'],2)
  finally:o.close()
 def test_multiple_sinks_form_one_budget_feasible_parent_tree(self):
  f,rc=domain(5,[(0,1,1),(1,3,1),(1,4,2),(0,2,0),(2,3,0),(2,4,0)]);o=Oracle(f,rc,B,{1,2},{1})
  try:
   result=o.query(0,{3:2,4:3},set());self.assertEqual(result['kind'],'A_SUPPORT_PRIMAL');parents={}
   for sink,a in result['answers'].items():
    node=0
    for e in a['slots']:
     nxt=f['dest_ranks'][e]
     if nxt in parents:self.assertEqual(parents[nxt],node)
     parents[nxt]=node;node=nxt
    self.assertEqual(node,sink)
   self.assertEqual(parents[3],1);self.assertEqual(parents[4],1);self.assertIsNone(result['raw_certificate'])
  finally:o.close()
 def test_random_graphs_against_simple_path_enumeration(self):
  rng=random.Random(20261021)
  for trial in range(60):
   n=rng.randrange(3,8);edges=[(u,v,rng.randrange(7)) for u in range(n) for v in range(n) if u!=v and rng.randrange(4)==0];f,rc=domain(n,edges);channels=set(range(1,n-1));support={n for n in channels if rng.randrange(2)};blocked={v for v in channels if rng.randrange(5)==0};paths=[]
   def visit(u,seen,cost,outside):
    if u==n-1:paths.append((outside,cost));return
    for a,b,c in edges:
     if a==u and b not in seen and b not in blocked:visit(b,seen|{b},cost+c,outside+int(b in channels-support))
   visit(0,{0},0,0);o=Oracle(f,rc,B,channels,support)
   try:
    weighted=o._weighted(0,{n-1},frozenset(blocked))[n-1];self.assertEqual(weighted['reachable'],bool(paths))
    if paths:self.assertEqual((weighted['outside_A_visits'],weighted['raw_cost']),min(paths))
    budget=rng.randrange(20);result=o.query(0,{n-1:budget},blocked);feasible=bool(paths) and min(c for k,c in paths)<=budget;self.assertEqual(result['within_budget'],feasible);self.assertEqual(result['pruning_allowed'],not feasible)
    if not feasible:self.assertIsNotNone(result['raw_certificate'])
    self.assertEqual(tuple(o.preferred.cap),tuple(f['capacities']));self.assertEqual(tuple(o.raw.engine.cap),tuple(f['capacities']))
   finally:o.close()
 def test_masks_restore_on_preferred_backend_failure(self):
  f,rc=domain(3,[(0,1,1),(1,2,1)]);o=Oracle(f,rc,B,{1},{1})
  try:
   def fail(*a):raise RuntimeError('injected')
   o.preferred.search=fail
   with self.assertRaises(RuntimeError):o.query(0,{2:3},{1})
   self.assertEqual(tuple(o.preferred.cap),(1,1,1));self.assertEqual(tuple(o.raw.engine.cap),(1,1,1))
  finally:o.close()
if __name__=='__main__':unittest.main()
