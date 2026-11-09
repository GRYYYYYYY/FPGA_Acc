import json,tempfile,unittest
from pathlib import Path
from array import array
from prepared_rc_sink_bounds import PreparedRCSinkBounds
from pre_route_endpoints import sha
class PreparedBoundTests(unittest.TestCase):
 def test_pinned_context_readonly_and_tamper_reject(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);original=root/'original';original.write_bytes(b'input');payload=root/'sink_1.bin';payload.write_bytes(array('Q',[2,0]).tobytes())
   receipt={'schema':'ROUTECAST_EXACT_RC_SINK_BOUNDS_V1','graph_sha256':'a'*64,'scale':7,'nodes':2,'byteorder':'little','unreachable_sentinel':(1<<64)-1,'inputs_sha256':{str(original):sha(original)},'sinks':[{'sink':1,'payload':payload.name,'sha256':sha(payload),'certificate':{'all_distance_and_tight_path_checks_passed':True}}]};(root/'receipt.json').write_text(json.dumps(receipt));digest=sha(root/'receipt.json');bounds=PreparedRCSinkBounds(root,digest,'a'*64,7,2);self.assertEqual(list(bounds.get(1)),[2,0])
   with self.assertRaises(TypeError):bounds.get(1)[0]=3
   with self.assertRaises(ValueError):bounds.get(0)
   with self.assertRaises(ValueError):PreparedRCSinkBounds(root,'0'*64,'a'*64,7,2)
   with self.assertRaises(ValueError):PreparedRCSinkBounds(root,digest,'b'*64,7,2)
   payload.write_bytes(array('Q',[3,0]).tobytes())
   with self.assertRaises(ValueError):PreparedRCSinkBounds(root,digest,'a'*64,7,2).get(1)
   original.write_bytes(b'changed')
   with self.assertRaises(ValueError):PreparedRCSinkBounds(root,digest,'a'*64,7,2)
if __name__=='__main__':unittest.main()
