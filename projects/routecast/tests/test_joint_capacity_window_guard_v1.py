import datetime as dt,json,tempfile,unittest,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from joint_capacity_window_guard_v1 import assess,load_anchor,timestamp
class Window(unittest.TestCase):
 def setUp(self):self.a={'recorded_utc':'2026-10-21T03:17:53.862314+00:00','review_no_later_than_utc':'2026-10-24T03:17:53.862314+00:00'};self.start=timestamp(self.a['recorded_utc'])
 def test_exact_boundaries(self):
  self.assertTrue(assess(self.a,self.start)['new_exploratory_launch_permitted_by_time']);self.assertFalse(assess(self.a,self.start+dt.timedelta(days=2)-dt.timedelta(microseconds=1))['two_day_review_window_reached']);self.assertEqual(assess(self.a,self.start+dt.timedelta(days=2))['status'],'REVIEW_WINDOW_OPEN');self.assertTrue(assess(self.a,self.start+dt.timedelta(days=3)-dt.timedelta(microseconds=1))['new_exploratory_launch_permitted_by_time']);self.assertFalse(assess(self.a,self.start+dt.timedelta(days=3))['new_exploratory_launch_permitted_by_time'])
 def test_timezone_and_invalid_clock(self):
  now=self.start+dt.timedelta(days=3);self.assertFalse(assess(self.a,now.astimezone(dt.timezone(dt.timedelta(hours=8))))['new_exploratory_launch_permitted_by_time'])
  with self.assertRaises(ValueError):assess(self.a,now.replace(tzinfo=None))
  with self.assertRaises(ValueError):assess(self.a,self.start-dt.timedelta(seconds=1))
 def test_source_and_timestamp_mutation_rejected(self):
  with tempfile.TemporaryDirectory(dir='/tmp') as tmp:
   p=Path(tmp)/'source.json';p.write_text(json.dumps({'stop_loss':self.a}));anchor=dict(self.a,source=str(p),source_sha256=hashlib.sha256(p.read_bytes()).hexdigest());ap=Path(tmp)/'anchor.json';ap.write_text(json.dumps(anchor));self.assertEqual(load_anchor(ap)['recorded_utc'],self.a['recorded_utc']);p.write_text(p.read_text()+' ')
   with self.assertRaises(ValueError):load_anchor(ap)
   anchor['source_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();anchor['recorded_utc']='2026-10-22T03:17:53.862314+00:00';ap.write_text(json.dumps(anchor))
   with self.assertRaises(ValueError):load_anchor(ap)
if __name__=='__main__':unittest.main()
