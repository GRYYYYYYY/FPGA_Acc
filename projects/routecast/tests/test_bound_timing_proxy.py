import copy,unittest
from test_observed_timing_proxy import ProxyTests
from bound_timing_proxy import bind,evaluate

class BoundProxyTests(unittest.TestCase):
 def test_bound_context_detached_and_valid_delta(self):
  g,b,c,long=ProxyTests().fixture();bound=bind(g,b,c);c['paths'].clear()
  candidate={**b,'connections':[{**r,'physical_edge_ids':long} for r in b['connections']]}
  self.assertEqual(evaluate(g,b,candidate,bound)['observed_path_max_span_delta'],1)
 def test_reject_wrong_baseline_and_content(self):
  g,b,c,long=ProxyTests().fixture();bound=bind(g,b,c);changed=copy.deepcopy(b);changed['connections'][0]['physical_edge_ids']=long
  with self.assertRaises(ValueError):evaluate(g,changed,changed,bound)
  altered=copy.deepcopy(bound);altered['context']['paths'][0]['endpoint_groups'].append([7,0,5])
  with self.assertRaises(ValueError):evaluate(g,b,b,altered)
  with self.assertRaises(ValueError):evaluate(g,b,b,c)
 def test_reject_wrong_graph_and_group(self):
  g,b,c,_=ProxyTests().fixture();bound=bind(g,b,c);bound['graph_sha256']='other'
  with self.assertRaises(ValueError):evaluate(g,b,b,bound)
  c['paths'][0]['endpoint_groups']=[[999,0,5]]
  with self.assertRaises(ValueError):bind(g,b,c)
if __name__=='__main__':unittest.main()
