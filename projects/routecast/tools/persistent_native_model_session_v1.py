"""Serial authenticated RR/RC/compiled search lifetime with native owner epochs.

Warm model fixtures remain per-call. Native owner commit is internal physical
state, never a substitute for route publication, canonical or timing gates.
"""
import json
from pathlib import Path
from class_cached_rc_endpoint_context_v1 import load_endpoints
from compiled_criticality_tree_v1 import Graph,BINARY
from source_binding_v2 import closure
from pre_route_endpoints import sha
from native_owner_reconcile_session_v1 import Session as OwnerSession

class Session:
 def __init__(self,endpoint):
  self.closed=False;self.active=False;self.owner=None;self.base=None
  self.sources=closure([Path(__file__)])
  self.sources[str(BINARY)]=sha(BINARY)
  self.graph,self.digest,self.nodes,self.fields,self.rc,queries=load_endpoints(endpoint)
  self.search=Graph(self.fields,self.rc.increments,[self.rc.initial(n) for n in range(len(self.nodes))])
  metadata=json.loads(Path(endpoint).read_text())
  self.net_digest=metadata['inputs']['net']['sha256'];self.net_names=metadata['net_names']
  self.identities={q['connection_id']:q['net_id'] for q in queries}
  self.current_queries=None;self.binds=0
 def acquire(self,endpoint):
  if self.closed or self.active:raise RuntimeError('closed or active persistent session')
  before=sha(endpoint);doc=json.loads(Path(endpoint).read_text())
  if not all(sha(p)==h for p,h in self.sources.items()):raise ValueError('source/ABI epoch changed')
  if doc['graph_sha256']!=self.digest or doc['inputs']['graph']['sha256']!=self.digest or sha(self.graph)!=self.digest:raise ValueError('graph epoch changed')
  if doc['inputs']['net']['sha256']!=self.net_digest or doc['net_names']!=self.net_names:raise ValueError('netlist epoch changed')
  if not all(sha(v['path'])==v['sha256'] for v in doc['inputs'].values()):raise ValueError('endpoint input changed')
  queries=doc['connections'];ids={}
  for q in queries:
   cid=q['connection_id']
   if type(cid) is not int or cid in ids:raise ValueError('connection identity')
   ids[cid]=q['net_id']
   for key,kind in [('source','SOURCE'),('sink','SINK')]:
    n=q[key]
    if type(n) is not int or not 0<=n<len(self.nodes) or self.nodes[n].get('type')!=kind:raise ValueError('invalid endpoint')
  if ids!=self.identities:raise ValueError('CID/NET epoch changed')
  if sha(endpoint)!=before:raise ValueError('endpoint changed during bind')
  self.current_queries={q['connection_id']:dict(q) for q in queries}
  self.active=True;self.binds+=1
  return self.graph,self.digest,self.nodes,self.fields,self.rc,queries
 def bind_base(self,base):
  if not self.active:raise RuntimeError('no model lease')
  if self.base is None:self.base=base
  elif self.base!=base:raise ValueError('node-base epoch changed; rebuild session')
  return self.base
 def release(self):
  if self.closed or not self.active:raise RuntimeError('no active model lease')
  self.active=False
 def initialize_owner(self,paths,inventory):
  if self.closed or self.active or self.owner is not None or self.current_queries is None:raise RuntimeError('owner initialization lifecycle')
  if inventory.digest!=self.digest:raise ValueError('owner inventory epoch')
  self.owner=OwnerSession(paths,self.current_queries,inventory)
 def reconcile_native(self,paths,inventory,*,generation):
  if self.closed or self.active or self.owner is None:raise RuntimeError('native owner lifecycle')
  ticket,summary=self.owner.prepare(paths,self.current_queries,inventory,generation=generation)
  self.owner.commit(ticket,generation=generation)
  return summary
 def close(self):
  if self.owner is not None:self.owner.close()
  self.search.close();self.active=False;self.closed=True
