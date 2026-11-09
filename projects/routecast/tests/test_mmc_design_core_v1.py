import sys,unittest,tempfile,json,hashlib,xml.etree.ElementTree as E
from pathlib import Path
from array import array
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from compact_stream_rc_endpoint_context_v1 import Nodes
from mmc_design_core_v1 import Core
class Backend:
 def __init__(self,f,inc,initial):self.initial=tuple(initial);self.closed=False;self.total_stats=[0,0,0];self.last_stats=None;self.closes=0
 def close(self):
  if not self.closed:self.closes+=1
  self.closed=True
class FakeEpisode:
 def __init__(self,*args,core,token):
  self.core=core;self.token=token;g,d,n,f,rc,q=core._load(token,args[0]);base,_,self._bindings=core._inputs(token)
  self.graph=core._graph(token,f,rc.increments,[0]*len(f['capacities']));self.fields=f;self.nodes=n;self.queries=q
 def close(self):self.graph.close();self.core._release(self.token)
class Contract(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();p=Path(self.tmp.name);self.ep=p/'ep';self.g=p/'graph';self.g.write_bytes(b'fixture');self.digest=hashlib.sha256(b'fixture').hexdigest()
  self.ep.write_text(json.dumps({'inputs':{'graph':{'path':str(self.g),'sha256':self.digest}},'connections':[{'connection_id':0}]}));self.nodes=Nodes()
  for i in range(2):self.nodes.append(E.fromstring(f'<node id="{i}" type="SOURCE" capacity="1"><loc xlow="{i}"/></node>'))
  self.nodes.freeze();self.fields={k:array('Q',v) for k,v in dict(node_ids=[0,1],row_offsets=[0,1,1],edge_ids=[0],dest_ranks=[1],switch_ids=[0],costs=[1],capacities=[1,1]).items()};self.base=(1,1)
  def load(ep):return self.g,self.digest,self.nodes,self.fields,SimpleNamespace(fields=self.fields,rc=SimpleNamespace(fields=self.fields),increments=(1,)),[]
  def inputs(*args):return self.base,{}, {str(self.ep):hashlib.sha256(self.ep.read_bytes()).hexdigest()}
  self.core=Core(loader=load,input_loader=inputs,backend_factory=Backend,episode_factory=FakeEpisode);self.args=[str(self.ep),str(p/'out'),'base','timing','warm','local']
 def tearDown(self):self.core.close();self.tmp.cleanup()
 def test_reuse_no_alias_and_stale_lease(self):
  a=self.core.open(*self.args);owner=self.core._backend
  with self.assertRaises(RuntimeError):self.core.open(*self.args)
  a.queries[0]['connection_id']=9;self.fields['dest_ranks'][0]=0;self.nodes.columns[('loc','xlow')].obj[0]=999
  self.assertEqual(a.fields['dest_ranks'][0],1);self.assertEqual(a.nodes[0].find('loc').get('xlow'),'0')
  with self.assertRaises(TypeError):a.fields['dest_ranks'][0]=8
  with self.assertRaises(AttributeError):a.nodes.strings=()
  a.close();b=self.core.open(*self.args);self.assertIs(owner,self.core._backend);self.assertEqual(b.queries[0]['connection_id'],0);token=self.core._token;a.close();self.assertIs(token,self.core._token)
  with self.assertRaises(RuntimeError):getattr(a.graph,'initial')
  self.assertEqual(self.core.stats['graph_loads'],1);self.assertEqual(self.core.stats['backend_reuses'],1);b.close();self.assertFalse(owner.closed)
  self.core.close();self.assertTrue(owner.closed);self.assertEqual(owner.closes,1)
 def test_changed_configuration_or_file_rejected(self):
  a=self.core.open(*self.args);a.close();different=list(self.args);different[5]='all'
  with self.assertRaises(ValueError):self.core.open(*different)
  self.ep.write_text(self.ep.read_text().replace('connection_id','connection_ix'))
  with self.assertRaises(ValueError):self.core.open(*self.args)
 def test_base_mismatch_rejected(self):
  a=self.core.open(*self.args);a.close();self.base=(2,1)
  with self.assertRaises(ValueError):self.core.open(*self.args)
  self.assertIsNone(self.core._token)
 def test_core_close_releases_active_episode(self):
  a=self.core.open(*self.args);self.core.close();self.assertTrue(a.graph.closed);self.assertTrue(self.core._backend.closed)
  with self.assertRaises(RuntimeError):self.core.open(*self.args)
if __name__=='__main__':unittest.main()
