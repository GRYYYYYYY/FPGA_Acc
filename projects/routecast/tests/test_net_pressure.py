from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rr_graph import read_rr_graph
from net_pressure_sketch import NetPressure,net_union
from frozen_pressure_sketch import FrozenPressureSketch

class NetPressureTests(unittest.TestCase):
    def fixture(self):
        g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml');rows=[{'connection_id':0,'net_id':4,'source':10,'sink':50,'physical_edge_ids':[0,1,2,3]},{'connection_id':1,'net_id':4,'source':10,'sink':60,'physical_edge_ids':[0,1,2,4]},{'connection_id':2,'net_id':5,'source':70,'sink':50,'physical_edge_ids':[5,1,2,3]}];users={4:{10,20,30,40,50,60},5:{70,20,30,40,50}};p={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):sum(n in u for u in users.values()) for n in {10,20,30,40,50,60,70}}};return g,p
    def test_shared_trunk_subtract_once_and_materialized_equivalence(self):
        g,p=self.fixture();engine=NetPressure(g,p);users,demand=net_union(g,p);self.assertEqual(demand[30],2)
        for net,source,sinks in ((4,10,{50,60}),(5,70,{50})):
            for exclude in (False,True):
                background={n:v-int(exclude and n in users[net]) for n,v in demand.items()};expected=FrozenPressureSketch(g,background,g.sha256,256,len(g.nodes)).search(source,sinks);actual,key=engine.query(net,source,sinks,exclude);self.assertEqual(actual,expected);self.assertEqual(engine.query(net,source,sinks,exclude),(actual,key))
        self.assertNotEqual(engine.query(4,10,{50},False)[1],engine.query(4,10,{50},True)[1])
        p['connections'].clear();p['node_occupancy'].clear();self.assertEqual(engine.demand[30],2)
    def test_same_source_different_nets_have_distinct_contexts(self):
        g,p=self.fixture();p['connections'][2].update(source=10,physical_edge_ids=[0,1,2,3]);p['node_occupancy'].pop('70');p['node_occupancy']['10']=2
        engine=NetPressure(g,p)
        retain=engine.query(4,10,{50,60},False)[0]
        self.assertEqual(retain.paths[50],engine.query(5,10,{50},False)[0].paths[50])
        self.assertNotEqual(engine.query(4,10,{50},True)[1],engine.query(5,10,{50},True)[1])

    def test_reject_invalid_background_and_context(self):
        g,p=self.fixture();p['node_occupancy']['30']=3
        with self.assertRaises(ValueError):NetPressure(g,p)
        g,p=self.fixture();p['connections'][1]['physical_edge_ids']=[0,4]
        with self.assertRaises(ValueError):NetPressure(g,p)
        g,p=self.fixture();p['connections'][2]['net_id']=4
        with self.assertRaisesRegex(ValueError,'multiple source'):NetPressure(g,p)
        g,p=self.fixture();engine=NetPressure(g,p)
        with self.assertRaises(ValueError):engine.query(999,10,{50})
        with self.assertRaises(ValueError):engine.query(4,70,{50})
        with self.assertRaises(ValueError):engine.query(4,True,{50})
        with self.assertRaises(ValueError):engine.query(4,10,{50},1)

if __name__=='__main__':unittest.main()
