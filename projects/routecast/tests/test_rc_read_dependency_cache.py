import unittest
from rc_read_dependency_cache import RCReadDependencyCache
class CacheTests(unittest.TestCase):
 def test_context_demands_and_mutable_results(self):
  cache=RCReadDependencyCache(4);context='a'*64;result={'status':'FOUND','physical_edge_ids':[8],'cost':3}
  cache.store(1,context,{2:1},{2,3},result);result['physical_edge_ids'].append(9)
  self.assertIsNone(cache.lookup(1,'b'*64,{2:1}));self.assertIsNone(cache.lookup(1,context,{2:2}))
  value,reads=cache.lookup(1,context,{2:1,0:99});self.assertEqual(reads,frozenset({2,3}));self.assertEqual(value['physical_edge_ids'],[8])
  value['physical_edge_ids'].clear();self.assertEqual(cache.lookup(1,context,{2:1})[0]['physical_edge_ids'],[8])
 def test_failed_capture_preserves_record_and_nonrepeatable_status_not_stored(self):
  cache=RCReadDependencyCache(4);context='a'*64;result={'status':'LABEL_LIMIT'};cache.store(1,context,{},[],result);before=cache.records[1]
  for nodes,other in (({4},{}),({2},{2:-1}),({True},{})):
   with self.assertRaises(ValueError):cache.store(1,context,other,nodes,result)
   self.assertIs(cache.records[1],before)
  self.assertFalse(cache.store(1,context,{},[],{'status':'ALLOCATION_FAILURE'}));self.assertIs(cache.records[1],before)
 def test_private_snapshot_roundtrip(self):
  cache=RCReadDependencyCache(4);context='a'*64;cache.store(3,context,{2:1},{2},{'status':'FOUND','physical_edge_ids':[8]});payload=cache.payload()
  private=RCReadDependencyCache.restore(4,payload);self.assertEqual(private.payload(),payload)
  private.store(3,context,{2:2},{2},{'status':'LABEL_LIMIT'})
  self.assertEqual(cache.payload(),payload);self.assertIsNotNone(cache.lookup(3,context,{2:1}));self.assertIsNone(private.lookup(3,context,{2:1}))
  with self.assertRaises(ValueError):RCReadDependencyCache.restore(4,bytearray(payload))
if __name__=='__main__':unittest.main()
