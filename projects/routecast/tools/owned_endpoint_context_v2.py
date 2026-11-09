"""Explicit owned RR context reuse with fresh input hashes and mutation checks."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from class_cached_rc_endpoint_context_v1 import load_endpoints
from pre_route_endpoints import sha
class OwnedEndpointContext:
 def __init__(self,endpoint):
  self.context=load_endpoints(endpoint);self.graph=self.context[0].resolve();self.digest=self.context[1]
  self.fingerprint=self._fingerprint();self.reuses=0
 def _fingerprint(self):
  g,d,nodes,fields,rc,_=self.context;h=hashlib.sha256()
  for node in nodes:h.update(ET.tostring(node))
  for key in sorted(fields):h.update(key.encode());h.update(fields[key].tobytes())
  h.update(str(rc.scale).encode());h.update(str(rc.increments).encode())
  if rc.fields is not fields or rc.rc.fields is not fields:raise ValueError('CSR ownership changed')
  h.update(str(sorted(rc.initial_by_class.items())).encode())
  h.update(rc.rc.node_classes.tobytes());h.update(str(rc.rc.classes).encode());h.update(str(sorted(rc.rc.switches.items())).encode())
  return h.hexdigest()
 def load(self,endpoint):
  meta=json.loads(Path(endpoint).read_text())
  if not all(sha(v['path'])==v['sha256'] for v in meta['inputs'].values()):raise ValueError('endpoint input changed')
  if Path(meta['inputs']['graph']['path']).resolve()!=self.graph or meta['graph_sha256']!=self.digest:raise ValueError('graph epoch mismatch')
  if sha(self.graph)!=self.digest or self._fingerprint()!=self.fingerprint:raise ValueError('owned context changed')
  self.reuses+=1;g,d,n,f,rc,_=self.context
  return g,d,n,f,rc,meta['connections']
