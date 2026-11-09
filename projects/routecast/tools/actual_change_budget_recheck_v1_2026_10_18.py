"""Exact budget recheck only; not physical/canonical/native acceptance."""
from pathlib import Path
from fractions import Fraction
from types import MappingProxyType
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths

def mapped_paths(meta,route):
 observed={}
 for name,branches in physical_paths(route).items():
  for path in branches:
   key=(name,path[0][0],path[-1][0])
   if key in observed:raise ValueError('Ambiguous route endpoint')
   observed[key]=tuple(path)
 result={};keys=set()
 for q in meta['connections']:
  cid=q['connection_id'];key=(meta['net_names'][str(q['net_id'])],q['source'],q['sink'])
  if cid in result or key in keys:raise ValueError('Duplicate identity')
  keys.add(key)
  if key not in observed:raise ValueError('Missing endpoint')
  result[cid]=observed[key]
 if keys!=set(observed):raise ValueError('Unexpected endpoints')
 return result

def authenticate(meta):
 for entry in meta['inputs'].values():
  if sha(entry['path'])!=entry['sha256']:raise ValueError('Input epoch changed')

class BudgetRecheck:
 def __init__(self,meta,route,memo):
  authenticate(meta)
  self.graph=meta['graph_sha256'];self.net=meta['inputs']['net']['sha256']
  if self.graph!=memo.digest:raise ValueError('Wrong electrical epoch')
  self.route=Path(route);self.route_sha=sha(route)
  self.identity=MappingProxyType({q['connection_id']:(q['net_id'],meta['net_names'][str(q['net_id'])]) for q in meta['connections']})
  self.paths=MappingProxyType(mapped_paths(meta,route))
  with memo.batch():self.delays=MappingProxyType({cid:memo.delay(path) for cid,path in self.paths.items()})
  authenticate(meta)
  if sha(route)!=self.route_sha:raise ValueError('Old route changed during preparation')
 def evaluate(self,meta,route,budget,memo):
  authenticate(meta)
  if sha(self.route)!=self.route_sha:raise ValueError('Stale old route')
  if meta['graph_sha256']!=self.graph or memo.digest!=self.graph:raise ValueError('Changed graph/RC epoch')
  if meta['inputs']['net']['sha256']!=self.net:raise ValueError('Changed packed net epoch')
  identity={q['connection_id']:(q['net_id'],meta['net_names'][str(q['net_id'])]) for q in meta['connections']}
  if len(identity)!=len(meta['connections']) or identity!=self.identity:raise ValueError('Changed connection identity')
  digest=sha(route);paths=mapped_paths(meta,route);rows=[];changed=[]
  with memo.batch():
   for cid,path in sorted(paths.items()):
    if path==self.paths[cid]:delay=self.delays[cid]
    else:delay=memo.delay(path);changed.append(cid)
    limit=Fraction(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))
    if limit<0:raise ValueError('Negative budget')
    rows.append(dict(connection_id=cid,delay_seconds=str(delay),budget_ns=str(limit),budget_pass=delay*10**9<=limit))
  authenticate(meta)
  if sha(route)!=digest or sha(self.route)!=self.route_sha:raise ValueError('Route changed during recheck')
  return dict(rows=rows,changed_connection_ids=changed,reused_delays=len(rows)-len(changed),violation_ids=[x['connection_id'] for x in rows if not x['budget_pass']])
