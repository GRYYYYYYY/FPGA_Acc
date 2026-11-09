import unittest,tempfile,copy
from pathlib import Path
from streaming_prediction_audit import verify
XML='''<rr_graph><rr_nodes>
<node id="0" type="SOURCE" capacity="1"><loc xlow="0" xhigh="0" ylow="0" yhigh="0"/></node>
<node id="1" type="CHANX" capacity="1"><loc xlow="0" xhigh="2" ylow="0" yhigh="0"/></node>
<node id="2" type="SINK" capacity="1"><loc xlow="2" xhigh="2" ylow="0" yhigh="0"/></node>
</rr_nodes><rr_edges><edge src_node="0" sink_node="1" switch_id="0"/><edge src_node="1" sink_node="2" switch_id="0"/><edge src_node="1" sink_node="0" switch_id="0"/></rr_edges></rr_graph>'''
class WitnessTests(unittest.TestCase):
 def inputs(self,p):
  from pre_route_endpoints import sha
  rows=[{'connection_id':0,'net_id':7,'source':0,'sink':2}];e={'graph_sha256':sha(p),'connections':rows}
  prediction={'physical_graph_sha256':sha(p),'connections':[{**rows[0],'physical_edge_ids':[0,1],'method':'test'}],'node_occupancy':{'0':1,'1':1,'2':1},'methods':{'test':1},'requested':1,'completed':1}
  return e,prediction
 def test_good_and_bad_witnesses(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'rr.xml';p.write_text(XML);e,v=self.inputs(p);r=verify(p,e,v,topology=True);self.assertEqual(r['net_union_topology']['cyclic_net_count'],0);self.assertEqual(r['net_union_topology']['internal_reconvergent_net_count'],0);self.assertEqual(r['channel_net_span_sum'],3);self.assertEqual(r['all_type_overuse_units'],0)
   for path in ([1],[0,2,0,1],[0,9],[0,True],None):
    bad=copy.deepcopy(v);bad['connections'][0]['physical_edge_ids']=path
    with self.subTest(path=path),self.assertRaises(ValueError):verify(p,e,bad)
   for mutate in ('occupancy','endpoint','duplicate'):
    bad=copy.deepcopy(v)
    if mutate=='occupancy':bad['node_occupancy']['1']=2
    elif mutate=='endpoint':bad['connections'][0]['sink']=1
    else:bad['connections']*=2
    with self.subTest(mutate=mutate),self.assertRaises(ValueError):verify(p,e,bad)
 def test_disabled_resource_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'rr.xml';p.write_text(XML.replace('id="1" type="CHANX" capacity="1"','id="1" type="CHANX" capacity="0"'));e,v=self.inputs(p)
   with self.assertRaisesRegex(ValueError,'disabled resource'):verify(p,e,v)

 def test_valid_paths_with_reconvergent_union(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'rr.xml';xml=XML.replace('</rr_nodes>','<node id="3" type="CHANX" capacity="1"><loc xlow="0" xhigh="1" ylow="0" yhigh="0"/></node></rr_nodes>').replace('</rr_edges>','<edge src_node="0" sink_node="3" switch_id="0"/><edge src_node="3" sink_node="1" switch_id="0"/></rr_edges>');p.write_text(xml);e,v=self.inputs(p)
   e['connections'].append({**e['connections'][0],'connection_id':1});v['connections'].append({**v['connections'][0],'connection_id':1,'physical_edge_ids':[3,4,1]});v['requested']=v['completed']=2;v['methods']={'test':2};v['node_occupancy']['3']=1
   result=verify(p,e,v,topology=True)
   self.assertTrue(result['all_physical_and_union_checks_passed']);self.assertEqual(result['net_union_topology']['internal_reconvergent_net_count'],1)
