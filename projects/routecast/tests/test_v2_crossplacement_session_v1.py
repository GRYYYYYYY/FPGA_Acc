import sys,unittest,tempfile,json,hashlib,copy,xml.etree.ElementTree as E
from pathlib import Path
from array import array
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
import compact_persistent_native_model_session_v1 as original
from compact_stream_rc_endpoint_context_v1 import Nodes
from v2_crossplacement_session_v1 import Session
class Graph:
 def __init__(self,f,inc,initial):self.closed=False;self.handle=1;self.total_stats=[0,0,0];self.last_stats=None
 def close(self):self.closed=True;self.handle=None
class Contract(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();p=Path(self.tmp.name);self.g=p/'g';self.net=p/'net';self.g.write_bytes(b'graph');self.net.write_bytes(b'net');self.a=p/'a';self.b=p/'b'
  self.doc={'inputs':{k:{'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for k,f in [('graph',self.g),('net',self.net)]},'graph_sha256':hashlib.sha256(b'graph').hexdigest(),'net_names':{'5':'n'},'connections':[{'connection_id':0,'net_id':5,'source':0,'sink':1}]}
  self.a.write_text(json.dumps(self.doc));second=copy.deepcopy(self.doc);second['connections'][0]['sink']=2;self.b.write_text(json.dumps(second));self.nodes=Nodes()
  for i,k in enumerate(['SOURCE','SINK','SINK']):self.nodes.append(E.fromstring(f'<node id="{i}" type="{k}" capacity="1"><loc xlow="{i}"/></node>'))
  self.nodes.freeze();self.f={k:array('Q',v) for k,v in dict(node_ids=[0,1,2],row_offsets=[0,1,1,1],edge_ids=[0],dest_ranks=[1],switch_ids=[0],costs=[1],capacities=[1]*3).items()}
  rc=SimpleNamespace(fields=self.f,rc=SimpleNamespace(fields=self.f),increments=(1,),initial=lambda n:0)
  self.patches=[patch.object(original,'load_endpoints',return_value=(self.g,self.doc['graph_sha256'],self.nodes,self.f,rc,self.doc['connections'])),patch.object(original,'Graph',Graph)]
  for x in self.patches:x.start()
  self.base=(1,1,1)
  def predictor(ep,*args,session):
   *_,qs=session.acquire(ep);session.bind_base(self.base);answer=[dict(q) for q in qs];session.release();return answer
  self.s=Session(self.a,predictor=predictor)
 def tearDown(self):
  self.s.close()
  for x in reversed(self.patches):x.stop()
  self.tmp.cleanup()
 def run_ticket(self,path):return self.s.execute(self.s.reserve(path),'out','base','timing','warm')
 def test_crossplacement_and_stale_tickets(self):
  t=self.s.reserve(self.a)
  with self.assertRaises(RuntimeError):self.s.reserve(self.b)
  with self.assertRaises(RuntimeError):self.s.execute(copy.copy(t),'out','b','c','w')
  a=self.s.execute(t,'out','b','c','w');self.assertEqual(a[0]['sink'],1);b=self.run_ticket(self.b);self.assertEqual(b[0]['sink'],2);self.assertFalse(self.s.search.closed);self.assertEqual(self.s.binds,2)
  with self.assertRaises(RuntimeError):self.s.execute(t,'out','b','c','w')
 def test_readonly_graph_and_changed_reservation(self):
  self.f['dest_ranks'][0]=2;self.assertEqual(self.s.fields['dest_ranks'][0],1)
  with self.assertRaises(TypeError):self.s.fields['dest_ranks'][0]=2
  t=self.s.reserve(self.a);self.a.write_text(self.a.read_text().replace('"sink": 1','"sink": 2'))
  with self.assertRaises(ValueError):self.s.execute(t,'out','b','c','w')
  self.assertTrue(self.s.closed);self.assertTrue(self.s.search.closed)
 def test_design_and_cid_guard_failure_closes(self):
  d=copy.deepcopy(self.doc);d['connections'][0]['net_id']=6;self.b.write_text(json.dumps(d))
  with self.assertRaises(ValueError):self.run_ticket(self.b)
  self.assertTrue(self.s.closed)
 def test_base_guard_and_cancellation(self):
  t=self.s.reserve(self.a);self.s.cancel(t);self.run_ticket(self.a);self.base=(2,1,1)
  with self.assertRaises(ValueError):self.run_ticket(self.b)
  self.assertTrue(self.s.search.closed)
if __name__=='__main__':unittest.main()
