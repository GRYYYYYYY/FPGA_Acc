from dataclasses import replace
import unittest
from test_pin_pools import graph
from rr_graph import RREdge
from observed_timing_proxy import path_deltas

class ProxyTests(unittest.TestCase):
    def fixture(self):
        g=graph();g=replace(g,edges=g.edges+(RREdge(1,2,0,()),))
        edge=lambda a,b:next(i for i,e in enumerate(g.edges) if (e.source,e.sink)==(a,b))
        short=[edge(0,1),edge(1,3),edge(3,5)];long=[edge(0,1),edge(1,2),edge(2,4),edge(4,5)]
        base={'physical_graph_sha256':g.sha256,'connections':[dict(connection_id=i,net_id=7,source=0,sink=5,physical_edge_ids=short) for i in (0,1)]}
        context={'paths':[{'rank':1,'endpoint_groups':[[7,0,5]]}]};return g,base,context,long
    def test_equivalent_group_max_not_sum(self):
        g,b,c,long=self.fixture();candidate={**b,'connections':[{**b['connections'][0],'physical_edge_ids':long},b['connections'][1]]}
        result=path_deltas(g,b,candidate,c);self.assertEqual(result['observed_path_max_span_delta'],1);self.assertEqual(result['covered_groups'],1)
        self.assertEqual(path_deltas(g,b,b,c)['observed_path_max_span_delta'],0)
    def test_moved_source_joins_by_stable_ids(self):
        g,b,c,long=self.fixture();nodes=dict(g.nodes);nodes[6]=replace(nodes[0],id=6);e=g.edges[long[0]];g=replace(g,nodes=nodes,edges=g.edges+(RREdge(6,e.sink,e.switch_id,()),))
        candidate={**b,'connections':[{**r,'source':6,'physical_edge_ids':[len(g.edges)-1]+long[1:]} for r in b['connections']]}
        self.assertEqual(path_deltas(g,b,candidate,c)['observed_path_max_span_delta'],1)
    def test_identity_path_and_unknown_group_fail_closed(self):
        g,b,c,_=self.fixture()
        for candidate in ({**b,'connections':b['connections'][:1]},{**b,'connections':[{**r,'physical_edge_ids':None} for r in b['connections']]},{**b,'physical_graph_sha256':'changed'}):
            with self.assertRaises(ValueError):path_deltas(g,b,candidate,c)
        with self.assertRaises(ValueError):path_deltas(g,b,b,{'paths':[{'rank':1,'endpoint_groups':[[9,0,5]]}]})

if __name__=='__main__':unittest.main()
