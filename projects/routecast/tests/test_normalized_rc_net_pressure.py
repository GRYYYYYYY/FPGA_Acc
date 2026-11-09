from pathlib import Path
import sys,unittest
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import test_normalized_rc_base as blend
from normalized_rc_net_pressure import NormalizedRCNetPressure
from normalized_rc_pressure import NormalizedRCPressureSketch
class NetRCPressureTests(unittest.TestCase):
 def inputs(self):
  g=blend.NormalizedBlendTests().graph()
  rows=[{'connection_id':0,'net_id':0,'source':10,'sink':50,'physical_edge_ids':[0,1,2,3]}, {'connection_id':1,'net_id':0,'source':10,'sink':60,'physical_edge_ids':[0,1,2,4]}, {'connection_id':2,'net_id':1,'source':70,'sink':50,'physical_edge_ids':[5,1,2,3]}]
  demand=Counter()
  for net in (0,1):
   nodes=set()
   for r in rows:
    if r['net_id']==net:nodes.add(r['source']);nodes.update(g.edges[e].sink for e in r['physical_edge_ids'])
   demand.update(nodes)
  return g,{'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in demand.items()}}
 def test_materialized_reference_and_trunk_once(self):
  g,p=self.inputs();owner=NormalizedRCNetPressure(g,blend.TEXT,g.sha256,p,100)
  self.assertEqual(owner.demand[30],2);self.assertEqual(owner.full[30],400);self.assertEqual(owner.reduced[30],200)
  for net,source,sinks in [(0,10,{50,60}),(1,70,{50})]:
   for exclude in (False,True):
    demand={n:v-(1 if exclude and n in owner.users[net] else 0) for n,v in owner.demand.items()}
    reference=NormalizedRCPressureSketch(g,blend.TEXT,g.sha256,demand,g.sha256,100).search(source,sinks)
    result,context=owner.query(net,source,sinks,exclude)
    self.assertEqual(result,reference)
  self.assertNotEqual(owner.query(0,10,{50},False)[1],owner.query(0,10,{50},True)[1])
 def test_source_and_bad_union(self):
  g,p=self.inputs();owner=NormalizedRCNetPressure(g,blend.TEXT,g.sha256,p)
  with self.assertRaises(ValueError):owner.query(0,70,{50})
  p['node_occupancy']['30']=3
  with self.assertRaises(ValueError):NormalizedRCNetPressure(g,blend.TEXT,g.sha256,p)
if __name__=='__main__':unittest.main()
