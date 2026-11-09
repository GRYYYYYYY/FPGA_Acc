import copy,unittest
from test_net_union_topology import UnionTests
from net_union_commit_gate import check
class GateTests(unittest.TestCase):
 def fixture(self):
  g,p=UnionTests().fixture([[0,1,2],[0,1,2]])
  for i,r in enumerate(p['connections']):r.update(connection_id=i,sink=4)
  return g,p
 def test_retained_branch_conflict_no_mutation(self):
  g,p=self.fixture();before=copy.deepcopy(p);r={**p['connections'][0],'physical_edge_ids':[3,4,2]}
  result=check(g,p,[r]);self.assertFalse(result['accepted']);self.assertEqual(p,before);self.assertEqual(result['affected_nets'],[1])
 def test_whole_net_compatible_update(self):
  g,p=self.fixture();rows=[{**r,'physical_edge_ids':[3,4,2]} for r in p['connections']]
  self.assertTrue(check(g,p,rows)['accepted'])
 def test_wrong_endpoint_rejected(self):
  g,p=self.fixture()
  with self.assertRaises(ValueError):check(g,p,[{**p['connections'][0],'source':3}])
