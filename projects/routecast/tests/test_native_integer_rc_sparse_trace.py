import unittest
from fractions import Fraction as F
from test_integer_rc_budget_boundaries import IntegerBudgetBoundaries
from native_integer_rc_search import NativeIntegerRC
from native_integer_rc_sparse_trace import NativeIntegerRCSparseTrace
from csr_integer_budget_search import query

class TraceTests(unittest.TestCase):
 def test_trace_results_and_dependency_reset(self):
  rc,scaled,costs=IntegerBudgetBoundaries().graph([(0,3,10,F(1,7)),(0,1,1,F(1,7)),(1,2,1,F(1,7)),(2,3,0,F(2))]);scaled.fields['costs']=costs;scaled.fields['capacities']=[1]*4
  tracer=NativeIntegerRCSparseTrace(scaled);plain=NativeIntegerRC(scaled)
  for other in ({1:20},{},{}):
   tracer.set_other(other);plain.set_other(other)
   tracer.query(0,3,scaled.scale,100)
   for budget in (0,scaled.scale):
    for limit in (1,3,100):
     reads=set()
     def cost(u,i):
      v=scaled.fields['dest_ranks'][i]
      if costs[i]:reads.add(v)
      return costs[i]*(1+other.get(v,0))
     expected=query(scaled,0,3,budget,lambda u,i:True,cost,limit)
     actual,footprint=tracer.traced_query(0,3,budget,limit)
     self.assertEqual(actual,expected);self.assertEqual(actual,plain.query(0,3,budget,limit));self.assertEqual(footprint,frozenset(reads))
 def test_overflow_read_mark_precedes_return(self):
  rc,scaled,costs=IntegerBudgetBoundaries().graph([(0,1,(1<<64)-2,F(1,7)),(1,3,(1<<64)-2,F(1,7))]);scaled.fields['costs']=costs;scaled.fields['capacities']=[1]*4
  tracer=NativeIntegerRCSparseTrace(scaled);plain=NativeIntegerRC(scaled)
  for search in (tracer,plain):search.set_other({1:(1<<64)-1,3:(1<<64)-1})
  result,footprint=tracer.traced_query(0,3,scaled.scale)
  self.assertEqual(result,plain.query(0,3,scaled.scale));self.assertEqual(result['status'],'ARITHMETIC_LIMIT');self.assertEqual(footprint,frozenset({1,3}))
if __name__=='__main__':unittest.main()
