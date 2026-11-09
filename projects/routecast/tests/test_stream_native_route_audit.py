from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from stream_native_route_audit import audit
class StreamTests(unittest.TestCase):
 def route(self,switch=5):
  return f'Net 0 (n)\nNode: 10 SOURCE Switch: 5\nNode: 20 OPIN Switch: 5\nNode: 30 CHANX Switch: 5\nNode: 40 IPIN Switch: 5\nNode: 50 SINK Switch: -1\nNode: 40 IPIN Switch: {switch}\nNode: 50 SINK Switch: -1\n'
 def test_terminal_occurrences_union(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'route';p.write_text(self.route());r=audit(Path(__file__).parent/'fixtures/rr_semantics.xml',p);self.assertEqual(len(r['connections']),2);self.assertEqual(r['node_occupancy']['30'],1);self.assertEqual(r['required_distinct_arcs'],4)
 def test_repeated_sink_wrong_incoming_switch(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'route';p.write_text(self.route(999))
   with self.assertRaisesRegex(ValueError,'arc/switch absent'):audit(Path(__file__).parent/'fixtures/rr_semantics.xml',p)
if __name__=='__main__':unittest.main()
