"""Serial process-local SHA reuse for coherent filesystem version signatures.

Full content hashing on cold admission or version change; no disk cache. This
adapter changes only aliases of the original pre_route_endpoints.sha function.
"""
import sys,time
from pathlib import Path
from contextlib import contextmanager
from types import ModuleType
from pre_route_endpoints import sha as ORIGINAL_SHA
_ACTIVE=None

class Cache:
 def __init__(self,hash_function=ORIGINAL_SHA):
  self.hash_function=hash_function;self.entries={};self.adapter=self.digest;self.modules=set()
  self.stats=dict(calls=0,hits=0,misses=0,invalidations=0,unstable=0,stable_admitted_bytes=0,hash_seconds=0.0,version_check_seconds=0.0)
 @staticmethod
 def signature(path):
  st=path.stat()
  return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
 def digest(self,path):
  self.stats['calls']+=1;tick=time.perf_counter();resolved=Path(path).resolve();key=str(resolved)
  try:before=self.signature(resolved)
  finally:self.stats['version_check_seconds']+=time.perf_counter()-tick
  cached=self.entries.get(key)
  if cached is not None and cached[0]==before:
   self.stats['hits']+=1;return cached[1]
  if cached is not None:self.stats['invalidations']+=1;del self.entries[key]
  self.stats['misses']+=1;tick=time.perf_counter()
  try:digest=self.hash_function(resolved)
  finally:self.stats['hash_seconds']+=time.perf_counter()-tick
  tick=time.perf_counter()
  try:after=self.signature(resolved)
  finally:self.stats['version_check_seconds']+=time.perf_counter()-tick
  if before!=after:
   self.stats['unstable']+=1;raise RuntimeError('file changed during digest admission')
  self.entries[key]=(after,digest);self.stats['stable_admitted_bytes']+=after[2]
  return digest
 @contextmanager
 def installed(self):
  global _ACTIVE
  if _ACTIVE is not None:raise RuntimeError('digest adapters must be serial, not nested')
  import pre_route_endpoints
  if pre_route_endpoints.sha is not ORIGINAL_SHA:raise RuntimeError('unexpected SHA provider')
  _ACTIVE=self
  try:
   for module in tuple(sys.modules.values()):
    if isinstance(module,ModuleType) and vars(module).get('sha') is ORIGINAL_SHA:
     vars(module)['sha']=self.adapter;self.modules.add(module.__name__)
   yield self
  finally:
   for module in tuple(sys.modules.values()):
    if isinstance(module,ModuleType) and vars(module).get('sha') is self.adapter:
     vars(module)['sha']=ORIGINAL_SHA;self.modules.add(module.__name__)
   _ACTIVE=None
 def snapshot(self):return dict(self.stats,entries=len(self.entries),installed_modules=sorted(self.modules))
