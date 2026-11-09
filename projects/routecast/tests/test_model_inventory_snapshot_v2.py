import sys,unittest,tempfile,hashlib,xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from compact_stream_rc_endpoint_context_v1 import Nodes
from model_inventory_snapshot_v1 import capture as reference
from model_inventory_snapshot_v2 import capture
class Contract(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'graph';self.path.write_bytes(b'fixture');self.digest=hashlib.sha256(b'fixture').hexdigest();self.nodes=Nodes()
  for i in range(3):self.nodes.append(E.fromstring(f'<node id="{i}" type="SOURCE" capacity="1"><loc xlow="{i}" ylow="0"/></node>'))
  self.nodes.freeze();self.f=dict(node_ids=[0,1,2],row_offsets=[0,1,2,2],edge_ids=[1,0],dest_ranks=[2,0],switch_ids=[7,8],capacities=[1,1,1])
 def tearDown(self):self.tmp.cleanup()
 def test_exact_metadata_edges_and_no_mutable_alias(self):
  a=reference(self.path,self.digest,self.nodes,self.f);b=capture(self.path,self.digest,self.nodes,self.f)
  for i in range(3):self.assertEqual(a.nodes[i],b.nodes[i]);self.assertEqual(a.graph.nodes[i],b.graph.nodes[i])
  for i in range(2):self.assertEqual(a.edges[i],b.edges[i])
  self.f['dest_ranks'][0]=0
  self.nodes.columns[('loc','xlow')].obj[0]=999
  self.assertEqual(b.nodes[0][1]['xlow'],'0');self.assertEqual(b.edges[1],(0,2,7))
  with self.assertRaises(TypeError):b.nodes.columns['xlow'][0]=3
  with self.assertRaises(AttributeError):b.nodes.columns={}
  with self.assertRaises(TypeError):b.graph.nodes.values[0]=9
 def test_rejected_identity_and_metadata(self):
  for key,value in [('edge_ids',[0,0]),('dest_ranks',[3,0]),('row_offsets',[0,2,1,2]),('capacities',[1,2,1]),('node_ids',[1,0,2])]:
   f=dict(self.f);f[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):capture(self.path,self.digest,self.nodes,f)
  self.nodes.columns[('node','type')].obj[0]=0
  with self.assertRaises(ValueError):capture(self.path,self.digest,self.nodes,self.f)
 def test_whole_byte_graph_guard(self):
  s=capture(self.path,self.digest,self.nodes,self.f);self.path.write_bytes(b'changed')
  with self.assertRaises(ValueError):s.validate(self.path,self.digest)
if __name__=='__main__':unittest.main()
