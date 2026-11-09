"""Complete old route delay/edge import from owned authenticated immutable inventory."""
from fractions import Fraction
from native_route_ledger_import_compact import physical_paths
from stream_native_route_audit_unified_v1 import audit
from pre_route_endpoints import sha

def load(route,meta,inventory):
 graph=meta['inputs']['graph']['path'];before=sha(route)
 if inventory.digest!=meta['graph_sha256']:raise ValueError('Wrong graph epoch')
 if any(sha(v['path'])!=v['sha256'] for v in meta['inputs'].values()):raise ValueError('Input epoch changed')
 proof=audit(graph,route,inventory)
 if proof['overflow_units']:raise ValueError('Old route capacity overflow')
 observed={}
 for name,paths in physical_paths(route).items():
  for path in paths:
   key=(name,path[0][0],path[-1][0])
   if key in observed:raise ValueError('Ambiguous named endpoint')
   observed[key]=tuple(path)
 expected={};queries={}
 for q in meta['connections']:
  key=(meta['net_names'][str(q['net_id'])],q['source'],q['sink']);cid=q['connection_id']
  if key in expected or cid in queries:raise ValueError('Duplicate demand identity')
  expected[key]=cid;queries[cid]=q
 if set(expected)!=set(observed):raise ValueError('Incomplete route demands')
 state={cid:observed[key] for key,cid in expected.items()};rows=[]
 for cid,path in state.items():
  q=queries[cid]
  if path[0]!=(q['source'],None) or inventory.physical.nodes[q['source']][0]!='SOURCE' or inventory.physical.nodes[q['sink']][0]!='SINK':raise ValueError('Invalid terminals')
  if len({n for n,s in path})!=len(path):raise ValueError('Cyclic path')
  r,c=inventory.classes[inventory.node_classes[q['source']]];delay=r*c/2;edges=[]
  for (u,_),(v,s) in zip(path,path[1:]):
   key=(u,v,s)
   if inventory.arc_multiplicities.get(key)!=1:raise ValueError('Nonunique or absent physical arc')
   edges.append(inventory.physical.arcs[key]);r,c=inventory.classes[inventory.node_classes[v]];sr,td=inventory.electrical_switches[s];delay+=(sr+r/2)*c+td
  rows.append(dict(connection_id=cid,delay_seconds=str(delay),physical_edge_ids=edges))
 if sha(route)!=before or sha(graph)!=inventory.digest:raise ValueError('Route or graph changed during import')
 return state,rows,proof
