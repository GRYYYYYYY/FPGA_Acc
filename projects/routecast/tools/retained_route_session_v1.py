"""One authenticated immutable old-route import, per-update full retention decisions."""
import json
from fractions import Fraction as F
from pathlib import Path
from class_cached_rc_endpoint_session_v2 import load_endpoints
from load_complete_route_state_v1 import load_complete
from pre_route_endpoints import sha

class RetainedRouteSession:
 def __init__(self,old_endpoint,old_route):
  self.endpoint=Path(old_endpoint);self.route=Path(old_route)
  self.old=json.loads(self.endpoint.read_text())
  self.bindings={str(p):sha(p) for p in (self.endpoint,self.route)}
  self.bindings.update({v['path']:v['sha256'] for v in self.old['inputs'].values()})
  _,_,nodes,fields,rc,queries=load_endpoints(self.endpoint)
  _,rows,_=load_complete(self.route,self.old,nodes,fields,rc)
  self._queries={q['connection_id']:dict(q) for q in queries}
  if len(self._queries)!=len(queries):raise ValueError('Duplicate original connection')
  self._rows={r['connection_id']:(r['delay_integer'],tuple(r['physical_edge_ids'])) for r in rows}
  if set(self._rows)!=set(self._queries):raise ValueError('Incomplete old route')
  self.scale=rc.scale;self.imports=1;self.selections=0
  self._authenticate()
 def _authenticate(self):
  if not all(sha(p)==h for p,h in self.bindings.items()):raise ValueError('Old route epoch binding changed')
 def select(self,target_endpoint,budget_path):
  self._authenticate()
  target=json.loads(Path(target_endpoint).read_text());budget=json.loads(Path(budget_path).read_text())
  if not all(sha(v['path'])==v['sha256'] for v in target['inputs'].values()):raise ValueError('Target input binding changed')
  if target['graph_sha256']!=self.old['graph_sha256'] or target['inputs']['net']['sha256']!=self.old['inputs']['net']['sha256']:raise ValueError('Different graph or packed netlist epoch')
  queries={q['connection_id']:q for q in target['connections']}
  if len(queries)!=len(target['connections']) or set(queries)!=set(self._queries):raise ValueError('Changed connection identity coverage')
  retained=[];released=[]
  for cid,q in sorted(queries.items()):
   before=self._queries[cid]
   if q['net_id']!=before['net_id'] or target['net_names'][str(q['net_id'])]!=self.old['net_names'][str(before['net_id'])]:raise ValueError('Connection NET identity changed')
   if (q['source'],q['sink'])!=(before['source'],before['sink']):
    released.append(dict(connection_id=cid,reason='ENDPOINT_CHANGED'));continue
   delay,edges=self._rows[cid];value=F(delay,self.scale)
   limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))
   if limit<0:raise ValueError('Negative budget')
   if value*10**9>limit:
    released.append(dict(connection_id=cid,reason='TARGET_BUDGET_UNSAFE',delay_seconds=str(value),budget_ns=str(limit)));continue
   retained.append(dict(q,physical_edge_ids=list(edges),delay_seconds=str(value),budget_ns=str(limit)))
  self._authenticate();self.selections+=1
  return dict(retained=retained,released=released,bindings={**self.bindings,str(Path(target_endpoint)):sha(target_endpoint),str(Path(budget_path)):sha(budget_path)})
