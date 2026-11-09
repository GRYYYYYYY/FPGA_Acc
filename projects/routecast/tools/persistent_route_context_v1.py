"""Persistent authenticated CSR/search and path-audit context across endpoint updates."""
import json
from pathlib import Path
from class_cached_rc_endpoint_context_v1 import load_endpoints
from content_bound_path_audit_v1 import PathAudit
from native_bounded_wire_search_v1 import NativeBoundedSearch
from pre_route_endpoints import sha

class RouteContext:
 def __init__(self,endpoints):
  self.graph,self.digest,self.nodes,self.fields,self.rc,_=load_endpoints(endpoints)
  self.audit=PathAudit(self.graph,self.digest)
  self.length={}
  for n,node in enumerate(self.nodes):
   if node.get('type') in ('CHANX','CHANY'):
    loc=node.find('loc');self.length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
  self.search=NativeBoundedSearch(self.rc,self.length);self.closed=False
 def endpoints(self,path):
  if self.closed:raise ValueError('context closed')
  path=Path(path);before=sha(path);doc=json.loads(path.read_text())
  assert doc['graph_sha256']==self.digest
  assert doc['inputs']['graph']['sha256']==self.digest
  assert all(sha(row['path'])==row['sha256'] for row in doc['inputs'].values())
  assert sha(self.graph)==self.digest and sha(path)==before
  queries={row['connection_id']:row for row in doc['connections']}
  assert len(queries)==len(doc['connections'])
  for query in queries.values():
   self.rc.node(query['source']);self.rc.node(query['sink'])
  return queries
 def query(self,source,sink,budget,outside,kept,parents,max_labels=100000):
  if self.closed:raise ValueError('context closed')
  assert sha(self.graph)==self.digest
  scaled=budget*self.rc.scale
  result=self.search.query(source,sink,scaled.numerator//scaled.denominator,outside,kept,parents,max_labels,sum(self.length.values())+1)
  assert sha(self.graph)==self.digest
  return result
 def close(self):
  self.search.close();self.closed=True
