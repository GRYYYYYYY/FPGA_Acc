import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from retained_A_branch_candidate_v1 import candidate

def graph(n,edges):
 row=[0];dest=[];inc=[];ids={}
 for u in range(n):
  for a,b,c in edges:
   if a==u:ids[a,b]=len(dest);dest.append(b);inc.append(c)
  row.append(len(dest))
 return {'row_offsets':row,'dest_ranks':dest,'capacities':[1]*n},inc,ids
class Contract(unittest.TestCase):
 def setup_case(self,new_suffix_cost=1):
  f,inc,e=graph(7,[(0,1,2),(1,2,2),(2,3,1),(3,5,1),(2,4,1),(0,6,1),(6,2,1),(2,5,new_suffix_cost)])
  qs=[dict(connection_id=1,source=0,sink=4,budget=5,physical_edge_ids=[e[0,1],e[1,2],e[2,4]]),dict(connection_id=2,source=0,sink=5,budget=6,physical_edge_ids=[e[0,1],e[1,2],e[2,3],e[3,5]])]
  proposal={'kind':'TEST_PRIMAL','within_budget':True,'pruning_allowed':False,'raw_certificate':None,'weighted_searches':1,'raw_searches':0,'answers':{4:{'reachable':True,'slots':[e[0,6],e[6,2],e[2,4]],'raw_cost':3},5:{'reachable':True,'slots':[e[0,6],e[6,2],e[2,5]],'raw_cost':2+new_suffix_cost}}}
  return f,inc,e,qs,proposal
 def test_unaffected_skips_provider(self):
  f,inc,e,qs,p=self.setup_case()
  def forbidden():raise AssertionError('unnecessary search')
  out=candidate(f,inc,0,0,qs,set(),forbidden);self.assertEqual(out['kind'],'A_UNCHANGED_PRIMAL');self.assertEqual(out['weighted_searches'],0);self.assertEqual(out['retained_connection_ids'],[1,2])
 def test_rejoin_uses_existing_parent_prefix(self):
  f,inc,e,qs,p=self.setup_case();out=candidate(f,inc,0,0,qs,{3},lambda:p);self.assertEqual(out['kind'],'A_BRANCH_RETAINED_PRIMAL');self.assertEqual(out['answers'][4]['slots'],qs[0]['physical_edge_ids']);self.assertEqual(out['answers'][5]['slots'],[e[0,1],e[1,2],e[2,5]]);self.assertEqual(out['answers'][5]['raw_cost'],5);self.assertFalse(out['pruning_allowed']);self.assertIsNone(out['raw_certificate'])
 def test_prefix_budget_failure_keeps_whole_feasible_proposal(self):
  f,inc,e,qs,p=self.setup_case(4);out=candidate(f,inc,0,0,qs,{3},lambda:p);self.assertEqual(out['kind'],'TEST_PRIMAL');self.assertFalse(out['retention_succeeded']);self.assertFalse(out['pruning_allowed']);self.assertEqual(out['answers'],p['answers'])
 def test_no_false_prune_without_raw_certificate(self):
  f,inc,e,qs,p=self.setup_case()
  with self.assertRaises(ValueError):candidate(f,inc,0,0,qs,{3},lambda:{'within_budget':False,'pruning_allowed':True,'raw_certificate':None})
 def test_reject_invalid_proposal_instead_of_silent_mix(self):
  f,inc,e,qs,p=self.setup_case();p['answers'][5]['slots']=[e[0,1],e[1,2],e[2,5]];p['answers'][5]['raw_cost']=5
  with self.assertRaises(ValueError):candidate(f,inc,0,0,qs,{3},lambda:p)
 def test_original_reference_is_atomic_shared_tree(self):
  f,inc,e,qs,p=self.setup_case();qs[1]['physical_edge_ids']=[e[0,6],e[6,2],e[2,5]]
  with self.assertRaises(ValueError):candidate(f,inc,0,0,qs,{3},lambda:p)
if __name__=='__main__':unittest.main()
