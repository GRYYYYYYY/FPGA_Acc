import copy,unittest
from test_net_pressure import NetPressureTests
from atomic_pressure_recompute import recompute
from net_pressure_sketch import NetPressure

class AtomicPressureTests(unittest.TestCase):
    def fixture(self):
        g,p=NetPressureTests().fixture()
        for r in p['connections']:r['method']='lifted'
        p.update(methods={'lifted':3},requested=3,completed=3)
        e={'graph_sha256':g.sha256,'connections':[{k:r[k] for k in ('connection_id','net_id','source','sink')} for r in p['connections']]}
        return g,e,p
    def test_selected_whole_net_and_frozen_inputs(self):
        g,e,p=self.fixture();saved=copy.deepcopy(p)
        a,r=recompute(g,e,p,[4],alpha=0)
        expected=NetPressure(g,p,0).query(4,10,{50,60})[0].paths
        self.assertEqual(r['recomputed_connections'],2)
        self.assertEqual(a['connections'][2],p['connections'][2])
        for row in a['connections'][:2]:self.assertEqual(tuple(row['physical_edge_ids']),expected[row['sink']])
        self.assertEqual(p,saved)
        self.assertEqual(recompute(g,e,p,[4],alpha=0),(a,r))
    def test_unknown_net_rejected_without_mutation(self):
        g,e,p=self.fixture();saved=copy.deepcopy(p)
        with self.assertRaises(ValueError):recompute(g,e,p,[999])
        self.assertEqual(p,saved)
    def test_pressure_configuration_changes_authenticated_context(self):
        g,e,p=self.fixture()
        _,a=recompute(g,e,p,[4],alpha=0);_,b=recompute(g,e,p,[4],alpha=256)
        self.assertNotEqual(a['contexts'],b['contexts'])
