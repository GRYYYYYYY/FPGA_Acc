"""Canonical immutable snapshot restore with a single dependency validation pass."""
import json
from rc_read_dependency_cache import RCReadDependencyCache,Record

class DirectRestoreRCReadDependencyCache(RCReadDependencyCache):
 @classmethod
 def restore(cls,nodes,payload):
  if type(payload) is not bytes:raise ValueError('immutable cache payload required')
  cache=cls(nodes)
  if not payload:return cache
  for slot,context,demands,result in json.loads(payload):
   if slot in cache.records:raise ValueError('duplicate cache slot')
   cache._context(context)
   if result['status'] not in ('FOUND','UNREACHABLE','LABEL_LIMIT','ARITHMETIC_LIMIT'):raise ValueError('unsupported cached status')
   captured=[];previous=-1
   for n,v in demands:
    if type(n) is not int or not previous<n<nodes or type(v) is not int or not 0<=v<(1<<64):raise ValueError('invalid canonical dependency')
    captured.append((n,v));previous=n
   result_bytes=json.dumps(result,allow_nan=False,separators=(',',':')).encode()
   cache.records[slot]=Record(context,tuple(captured),result_bytes)
  return cache
