"""Reject valid but unrelated evaluator inputs, and changed archived sources."""
import unittest,tempfile,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from pre_route_endpoints import sha
from compare_koios_matched import load_evidence

class EvidenceBinding(unittest.TestCase):
 def test_binding_and_source_tamper(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);p=root/'prediction';e=root/'evaluation';p.mkdir();e.mkdir();(e/'source').mkdir()
   def save(path,value):path.write_text(json.dumps(value))
   graph=root/'graph.xml';graph.write_text('<graph/>');g={'path':str(graph),'sha256':sha(graph)}
   for name in ['prediction','endpoints']:save(p/(name+'.json'),{})
   save(p/'protocol.json',{'inputs':{'rr_graph.xml':g}})
   save(p/'receipt.json',{'protocol_sha256':sha(p/'protocol.json'),'outputs':{name+'.json':sha(p/(name+'.json')) for name in ['prediction','endpoints']},'audit':{'requested':15138,'all_physical_and_union_checks_passed':True},'inputs_unchanged':True,'failed_connections':0})
   (e/'source'/'evaluator.py').write_text('original')
   ep={'inputs':{'graph':g,**{name:{'path':str(p/(name+'.json')),'sha256':sha(p/(name+'.json'))} for name in ['prediction','endpoints']}},'source_sha256':{'evaluator.py':sha(e/'source'/'evaluator.py')}}
   save(e/'spatial_maps.json',{});save(e/'protocol.json',ep)
   er={'protocol_sha256':sha(e/'protocol.json'),'exact_full15138_native_endpoint_multiset':True,'inputs_unchanged':True,'reports':{'failed_connections':0},'spatial_maps_sha256':sha(e/'spatial_maps.json')};save(e/'receipt.json',er)
   load_evidence(p,e)
   other=root/'other_prediction.json';other.write_bytes((p/'prediction.json').read_bytes());ep['inputs']['prediction']['path']=str(other)
   save(e/'protocol.json',ep);er['protocol_sha256']=sha(e/'protocol.json');save(e/'receipt.json',er)
   with self.assertRaisesRegex(ValueError,'another predictor'):load_evidence(p,e)
   ep['inputs']['prediction']['path']=str(p/'prediction.json');save(e/'protocol.json',ep);er['protocol_sha256']=sha(e/'protocol.json');save(e/'receipt.json',er)
   (e/'source'/'evaluator.py').write_text('changed')
   with self.assertRaisesRegex(ValueError,'source changed'):load_evidence(p,e)

if __name__=='__main__':unittest.main()
