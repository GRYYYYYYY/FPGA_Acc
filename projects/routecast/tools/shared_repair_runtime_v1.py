"""Single explicit parent-owned immutable graph and native search lifetime."""
from immutable_endpoint_context_v1 import ImmutableEndpointContext
from native_immutable_bounded_search_v1 import NativeBoundedSearch as Engine
_context=None
_engine=None
leases=0
class Lease:
 def __getattr__(self,key):return getattr(_engine,key)
 def close(self):pass
def load_endpoints(path):
 global _context
 if _context is None:_context=ImmutableEndpointContext.build(path)
 return _context.load(path)
def NativeBoundedSearch(rc,length):
 global _engine,leases
 if _context is None or rc is not _context.rc:raise ValueError('foreign context')
 if _engine is None:_engine=Engine(rc,length)
 if dict(_engine.length)!=length:raise ValueError('geometry mismatch')
 leases+=1;return Lease()
def shutdown():
 global _engine,_context
 if _engine is not None:_engine.close()
 _engine=None;_context=None
