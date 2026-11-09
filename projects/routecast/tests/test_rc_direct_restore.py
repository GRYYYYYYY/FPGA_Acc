import json,unittest
from rc_read_dependency_cache import RCReadDependencyCache
from rc_read_dependency_cache_direct_restore import DirectRestoreRCReadDependencyCache
class RestoreTests(unittest.TestCase):
 def test_canonical_roundtrip_and_private_publication(self):
  original=RCReadDependencyCache(4);original.store(3,'a'*64,{1:2},{3,1},{'status':'FOUND','physical_edge_ids':[8]});payload=original.payload()
  restored=DirectRestoreRCReadDependencyCache.restore(4,payload);self.assertEqual(restored.payload(),payload);self.assertEqual(restored.lookup(3,'a'*64,{1:2}),original.lookup(3,'a'*64,{1:2}))
  restored.store(3,'a'*64,{},[],{'status':'LABEL_LIMIT'});self.assertEqual(original.payload(),payload)
 def test_malformed_snapshot_rejected(self):
  for demands in ([[1,0],[1,0]],[[2,0],[1,0]],[[4,0]],[[True,0]],[[1,False]],[[1,-1]],[[1,1<<64]]):
   payload=json.dumps([[3,'a'*64,demands,{'status':'FOUND'}]]).encode()
   with self.assertRaises(ValueError):DirectRestoreRCReadDependencyCache.restore(4,payload)
  for records in ([[3,'a'*64,[],{'status':'ALLOCATION_FAILURE'}]],[[3,'a'*64,[],{'status':'FOUND'}]]*2):
   with self.assertRaises(ValueError):DirectRestoreRCReadDependencyCache.restore(4,json.dumps(records).encode())
if __name__=='__main__':unittest.main()
