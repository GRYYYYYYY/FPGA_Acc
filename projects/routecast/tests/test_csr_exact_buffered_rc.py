import unittest
from fractions import Fraction as F
from csr_exact_buffered_rc import ExactBufferedRC
class Test(unittest.TestCase):
 def engine(self):
  fields={'node_ids':[0,1,2],'row_offsets':[0,2,3,3],'edge_ids':[4,1,8],'dest_ranks':[1,2,2],'switch_ids':[0,0,0]}
  return ExactBufferedRC(fields,[0,1,1],[(F(2),F(3)),(F(4),F(5))],{0:(F(1,2),F(1))})
 def test_exact_sparse_parallel_alternatives(self):
  rc=self.engine();self.assertEqual(rc.path(0,2,[4,8]),F(30));self.assertEqual(rc.path(0,2,[1]),F(33,2));self.assertEqual(len(rc.cache),1)
 def test_invalid(self):
  rc=self.engine()
  for source,sink,path in [(0,2,[8]),(0,1,[1]),(True,2,[1]),(0,2,[True]),(0,2,[-1])]:
   with self.assertRaises(ValueError):rc.path(source,sink,path)
if __name__=='__main__':unittest.main()
