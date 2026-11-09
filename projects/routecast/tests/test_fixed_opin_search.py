import unittest
from fractions import Fraction as F
from csr_exact_buffered_rc import ExactBufferedRC
from csr_integer_exact_delay import IntegerRC
from fixed_opin_search import fixed_opin_query
class Test(unittest.TestCase):
 def context(self):
  # OPIN 1 is slower than OPIN 2; parallel SOURCE arcs remain distinct.
  fields={'node_ids':list(range(4)),'types':[0,2,2,1],'row_offsets':[0,3,4,5,5],'dest_ranks':[1,1,2,3,3],'edge_ids':[0,1,2,3,4],'switch_ids':[0,1,2,3,4]}
  switches={i:(F(0),F(v)) for i,v in enumerate([3,2,0,1,0])}
  return IntegerRC(ExactBufferedRC(fields,[0]*4,[(F(2),F(1))],switches))
 def test_selected_and_source_delay(self):
  c=self.context();r=fixed_opin_query(c,0,3,1,F(20),lambda n,i:True)
  self.assertEqual(r['physical_edge_ids'],[1,3]);self.assertEqual(r['delay'],F(6))
  self.assertEqual(fixed_opin_query(c,0,3,1,F(5),lambda n,i:True)['status'],'UNREACHABLE')
 def test_parallel_and_external_constraint(self):
  r=fixed_opin_query(self.context(),0,3,1,F(20),lambda n,i:i!=1)
  self.assertEqual(r['physical_edge_ids'],[0,3])
 def test_limit_and_identity(self):
  self.assertEqual(fixed_opin_query(self.context(),0,3,1,F(20),lambda n,i:True,max_nodes=1)['status'],'NODE_LIMIT')
  with self.assertRaises(ValueError):fixed_opin_query(self.context(),0,3,3,F(20),lambda n,i:True)
if __name__=='__main__':unittest.main()
