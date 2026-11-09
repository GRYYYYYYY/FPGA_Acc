import unittest
from types import SimpleNamespace as S
from net_union_topology import diagnose
class UnionTests(unittest.TestCase):
 def fixture(self,paths):
  arcs=[(0,1),(1,2),(2,4),(0,3),(3,2),(2,1),(1,4)]
  g=S(sha256='g',nodes={i:S(type='SOURCE' if i==0 else 'SINK' if i==4 else 'CHANX') for i in range(5)},edges=[S(source=a,sink=b) for a,b in arcs])
  p={'physical_graph_sha256':'g','connections':[{'net_id':1,'source':0,'physical_edge_ids':path} for path in paths]};return g,p
 def test_shared_prefix_not_reconvergence(self):
  r=diagnose(*self.fixture([[0,1,2],[0,6]]));self.assertEqual(r['internal_reconvergent_net_count'],0);self.assertEqual(r['terminal_alias_net_count'],1);self.assertEqual(r['cyclic_net_count'],0)
 def test_two_simple_paths_can_form_union_cycle(self):
  r=diagnose(*self.fixture([[0,1,2],[3,4,5,6]]));self.assertEqual(r['cyclic_net_count'],1);self.assertEqual(r['internal_reconvergent_net_count'],1)
 def test_dag_reconvergence(self):
  r=diagnose(*self.fixture([[0,1,2],[3,4,2]]));self.assertEqual(r['cyclic_net_count'],0);self.assertEqual(r['internal_reconvergent_net_count'],1)
if __name__=='__main__':unittest.main()
