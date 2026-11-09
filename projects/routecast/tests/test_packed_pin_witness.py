import copy,unittest
from test_pin_choice_catalog import CatalogTests
from packed_pin_witness import join
class PackedWitnessTests(unittest.TestCase):
 def fixture(self):
  g=CatalogTests().fixture();rows=[dict(connection_id=i,net_id=7,source=0,sink=6) for i in range(2)];e={'graph_sha256':g.sha256,'connections':rows};p={'physical_graph_sha256':g.sha256,'connections':[{**rows[0],'physical_edge_ids':[0,2,4,6],'method':'lifted'},{**rows[1],'physical_edge_ids':[1,3,5,7],'method':'lifted'}],'node_occupancy':{str(n):1 for n in range(7)},'methods':{'lifted':2},'requested':2,'completed':2}
  details=[dict(net_id=7,block='driver',port='O',bit=0,role='SOURCE',rr_node=0,physical_pin_ptc=1)]+[dict(net_id=7,block='receiver',port='I',bit=i,role='SINK',rr_node=6,physical_pin_ptc=i) for i in range(2)];return g,e,{'pin_details':details},p
 def test_equivalent_sink_order_and_nominal_source_difference(self):
  args=self.fixture();r=join(*args);self.assertEqual([x['packed_sink']['bit'] for x in r],[0,1]);self.assertTrue(all(x['selected_ipin_matches_nominal_ptc'] for x in r));self.assertFalse(r[0]['selected_opin_matches_nominal_ptc']);self.assertEqual(join(*args),r)
 def test_invalid_class_member_rejected_without_mutation(self):
  args=self.fixture();args[2]['pin_details'][1]['physical_pin_ptc']=99;saved=copy.deepcopy(args[2])
  with self.assertRaises(ValueError):join(*args)
  self.assertEqual(args[2],saved)
 def test_duplicate_or_missing_pin_rejected(self):
  args=self.fixture();args[2]['pin_details'].append(dict(args[2]['pin_details'][1]))
  with self.assertRaises(ValueError):join(*args)
  args=self.fixture();args[2]['pin_details'].pop()
  with self.assertRaises(ValueError):join(*args)
