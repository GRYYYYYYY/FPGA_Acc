import sys,unittest,tempfile,json,hashlib,copy,xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from model_inventory_snapshot_v1 import capture
from serialize_whole_net_subset_pin_index_v2 import serialize_subset
from net_fragment_serializer_v1 import Session
class Contract(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();p=Path(self.tmp.name);self.graph=p/'graph';self.graph.write_bytes(b'fixture');digest=hashlib.sha256(b'fixture').hexdigest()
  nodes=[E.fromstring(f'<node id="{i}" type="{kind}" capacity="1"><loc xlow="{i}" xhigh="{i}" ylow="0" yhigh="0" layer="0" ptc="0"/></node>') for i,kind in enumerate(['SOURCE','CHANX','CHANX','SINK'])]
  fields=dict(node_ids=[0,1,2,3],row_offsets=[0,2,3,4,4],edge_ids=[0,2,1,3],dest_ranks=[1,2,3,3],switch_ids=[0]*4,capacities=[1]*4)
  self.inventory=capture(self.graph,digest,nodes,fields);self.ep=p/'ep.json';self.ident=p/'identity';self.place=p/'place';self.place.write_text('header\nArray size: 4 x 1 logic blocks\n')
  self.q={'connection_id':0,'net_id':10,'source':0,'sink':3};self.meta={'inputs':{'graph':{'path':str(self.graph),'sha256':digest}},'graph_sha256':digest,'net_names':{'10':'n'},'connections':[self.q]};self.ep.write_text(json.dumps(self.meta))
  self.native={'name':'n','net_id':5,'pins':[{'index':0,'x':0,'y':0,'layer':0,'class':0},{'index':1,'x':3,'y':0,'layer':0,'class':0}]};self.ident.write_text(json.dumps(self.native)+'\n')
  self.c={'records':[{**self.q,'answer':{'physical_edge_ids':[0,1]}}]};self.args=(self.ep,self.ident,self.place,self.inventory)
 def tearDown(self):self.tmp.cleanup()
 def equal(self,s,c=None):
  c=self.c if c is None else c;actual=s.serialize(c,*self.args);self.assertEqual(actual,serialize_subset(c,*self.args));return actual
 def test_hits_path_change_and_immutable_key(self):
  s=Session();a=self.equal(s);self.equal(s);self.assertEqual(s.stats['hits'],1)
  self.c['records'][0]['answer']['physical_edge_ids'][:]=[2,3];b=self.equal(s);self.assertNotEqual(a,b);self.assertEqual(s.stats['misses'],2)
  self.c['records'][0]['answer']['physical_edge_ids'][:]=[0,1];self.assertEqual(self.equal(s),a);self.assertEqual(s.stats['hits'],2)
 def test_identity_and_header_changes(self):
  s=Session();a=self.equal(s);self.native['pins'][1]['index']=2;self.ident.write_text(json.dumps(self.native)+'\n');b=self.equal(s);self.assertNotEqual(a,b);self.assertEqual(s.stats['misses'],2)
  self.place.write_text('newheader\nArray size: 4 x 1 logic blocks\n');self.assertNotEqual(self.equal(s)[0],b[0]);self.assertEqual(s.stats['hits'],1)
 def test_invalid_current_input_cannot_use_hit(self):
  s=Session();self.equal(s)
  self.native['pins'][1]['x']=2;self.ident.write_text(json.dumps(self.native)+'\n')
  with self.assertRaises(ValueError):s.serialize(self.c,*self.args)
  self.ident.write_text(json.dumps({**self.native,'pins':[self.native['pins'][0],{**self.native['pins'][1],'x':3}]})+'\n');self.graph.write_bytes(b'changed')
  with self.assertRaises(ValueError):s.serialize(self.c,*self.args)
 def test_failed_request_does_not_publish_new_fragments(self):
  s=Session();self.equal(s);before=len(s._entries)
  q={**self.q,'connection_id':1,'net_id':11};self.meta['connections'].append(q);self.meta['net_names']['11']='m';self.ep.write_text(json.dumps(self.meta));self.ident.write_text(json.dumps(self.native)+'\n'+json.dumps({**self.native,'name':'m','net_id':6})+'\n')
  c=copy.deepcopy(self.c);c['records'][0]['answer']['physical_edge_ids']=[2,3];c['records'].append({**q,'answer':{'physical_edge_ids':[3]}})
  with self.assertRaises(ValueError):s.serialize(c,*self.args)
  self.assertEqual(len(s._entries),before);self.assertIsNone(s._pending)
 def test_partial_NET_and_bounded_cache(self):
  s=Session(max_entries=1);self.equal(s);self.c['records'][0]['answer']['physical_edge_ids']=[2,3];self.equal(s);self.assertEqual(s.stats['evictions'],1)
  self.meta['connections'].append({**self.q,'connection_id':2});self.ep.write_text(json.dumps(self.meta))
  with self.assertRaises(ValueError):s.serialize(self.c,*self.args)
if __name__=='__main__':unittest.main()
