import unittest
from types import SimpleNamespace as S
from collections import Counter
from sketch_resource_neighborhood import resource_neighborhood

class NeighborhoodTests(unittest.TestCase):
    def fixture(self):
        nodes={i:S(type='SOURCE' if i<3 else 'SINK' if i<6 else 'CHANX') for i in range(8)}
        edges=[S(source=a,sink=b) for a,b in [(0,6),(6,3),(1,6),(6,7),(7,4),(2,7),(7,5)]]
        g=S(sha256='g',nodes=nodes,edges=edges)
        rows=[dict(connection_id=i,net_id=i,source=i,sink=i+3) for i in range(3)]
        e={'graph_sha256':'g','connections':rows}
        paths=[[0,1],[2,3,4],[5,6]];users={}
        for r,path in zip(rows,paths):
            for n in {r['source']}|{edges[k].sink for k in path}:users.setdefault(str(n),set()).add(r['net_id'])
        p={'physical_graph_sha256':'g','connections':[{**r,'physical_edge_ids':path,'method':'lifted'} for r,path in zip(rows,paths)],'node_occupancy':{n:len(v) for n,v in users.items()},'methods':{'lifted':3},'requested':3,'completed':3}
        # Seed via added connection to existing net, with complete matching witness.
        after={**e,'connections':rows+[dict(rows[0],connection_id=3)]}
        q={**p,'connections':p['connections']+[dict(p['connections'][0],connection_id=3)],'methods':{'lifted':4},'requested':4,'completed':4}
        return g,e,after,p,q
    def test_hops_and_whole_net(self):
        args=self.fixture()
        self.assertEqual(resource_neighborhood(*args,hops=0)['expanded_net_ids'],[0])
        self.assertEqual(resource_neighborhood(*args,hops=1)['expanded_net_ids'],[0,1])
        r=resource_neighborhood(*args,hops=2)
        self.assertEqual(r['net_layers'],[[0],[1],[2]])
        self.assertEqual(r['recompute_connection_ids'],[0,1,2,3])
    def test_source_group_closes_without_resource_hop(self):
        g,e,a,p,q=self.fixture()
        g.edges[2].source=0
        for endpoint in (e,a):
            endpoint['connections'][1]['source']=0
        for prediction in (p,q):
            prediction['connections'][1]['source']=0
            prediction['node_occupancy']['0']=2
            prediction['node_occupancy'].pop('1',None)
        self.assertEqual(resource_neighborhood(g,e,a,p,q,hops=0)['expanded_net_ids'],[0,1])

    def test_noop(self):
        g,e,_,p,_=self.fixture()
        self.assertEqual(resource_neighborhood(g,e,e,p,p)['expanded_net_ids'],[])
    def test_reject_corrupt_witness_and_hops(self):
        args=self.fixture()
        with self.assertRaises(ValueError):resource_neighborhood(*args,hops=True)
        args[-1]['node_occupancy']={}
        with self.assertRaises(ValueError):resource_neighborhood(*args)
