import sys,unittest,tempfile,hashlib,xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from model_inventory_snapshot_v1 import capture
class Contract(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'graph';self.path.write_bytes(b'fixture');self.digest=hashlib.sha256(b'fixture').hexdigest()
  self.nodes=[E.fromstring(f'<node id="{i}" type="SOURCE" capacity="1"><loc xlow="{i}" ylow="0"/></node>') for i in range(3)]
  self.f=dict(node_ids=[0,1,2],row_offsets=[0,1,2,2],edge_ids=[1,0],dest_ranks=[2,0],switch_ids=[7,8],capacities=[1,1,1])
 def tearDown(self):self.tmp.cleanup()
 def test_identity_and_owned_immutability(self):
  s=capture(self.path,self.digest,self.nodes,self.f);self.assertEqual(s.edges[0],(1,0,8));self.assertEqual(s.edges[1],(0,2,7))
  self.f['dest_ranks'][0]=0;self.nodes[0].find('loc').set('xlow','99');self.assertEqual(s.edges[1],(0,2,7));self.assertEqual(s.nodes[0][1]['xlow'],'0')
  with self.assertRaises(TypeError):s.graph.edges.source[0]=9
  with self.assertRaises(TypeError):s.nodes[0][1]['xlow']='9'
  with self.assertRaises(AttributeError):s.graph.edges.source=()
 def test_invalid_columns_and_mapping(self):
  for key,value in [('edge_ids',[0,0]),('edge_ids',[0,2]),('dest_ranks',[3,0]),('row_offsets',[0,2,1,2]),('capacities',[1,2,1]),('node_ids',[1,0,2])]:
   f=dict(self.f);f[key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):capture(self.path,self.digest,self.nodes,f)
 def test_same_size_graph_rewrite(self):
  s=capture(self.path,self.digest,self.nodes,self.f);self.path.write_bytes(b'changed')
  with self.assertRaises(ValueError):s.validate(self.path,self.digest)
if __name__=='__main__':unittest.main()
