"""Complete named-endpoint route import with original CSR arcs and exact RC.

Requires a graph context authenticated by load_endpoints. Packed-pin equivalence
and native STA remain separate obligations; ambiguous named endpoints fail.
"""
from collections import Counter
from native_route_ledger_import_compact import physical_paths
from incremental_shared_tree_ledger_v1 import SharedTreeLedger
from pre_route_endpoints import sha

def load_complete(route,meta,nodes,fields,rc):
 before=sha(route);observed={}
 for name,paths in physical_paths(route).items():
  for path in paths:
   key=(name,path[0][0],path[-1][0])
   if key in observed:raise ValueError('ambiguous repeated named endpoint')
   observed[key]=tuple(path)
 queries={q['connection_id']:q for q in meta['connections']}
 if len(queries)!=len(meta['connections']):raise ValueError('duplicate connection id')
 expected={}
 for cid,q in queries.items():
  key=(meta['net_names'][str(q['net_id'])],q['source'],q['sink'])
  if key in expected:raise ValueError('ambiguous endpoint mapping')
  expected[key]=cid
 if set(expected)!=set(observed):raise ValueError('missing or unexpected route demands')
 state={cid:observed[key] for key,cid in expected.items()};needed=set()
 for cid,path in state.items():
  q=queries[cid]
  if path[0]!=(q['source'],None) or nodes[q['source']].get('type')!='SOURCE' or nodes[q['sink']].get('type')!='SINK':raise ValueError('invalid terminal types')
  if len({n for n,s in path})!=len(path):raise ValueError('cyclic branch')
  for n,s in path:
   if type(n) is not int or not 0<=n<len(nodes) or fields['capacities'][n]<=0:raise ValueError('invalid branch node')
  needed.update((u,v,s) for (u,_),(v,s) in zip(path,path[1:]))
 matches={key:[] for key in needed}
 for u in sorted({u for u,v,s in needed}):
  for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
   key=(u,fields['dest_ranks'][slot],fields['switch_ids'][slot])
   if key in matches:matches[key].append(fields['edge_ids'][slot])
 if any(len(ids)!=1 for ids in matches.values()):raise ValueError('nonunique or absent original physical arc')
 length={}
 for n,node in enumerate(nodes):
  if node.get('type') in ('CHANX','CHANY'):
   loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
 ledger=SharedTreeLedger(state,queries,fields['capacities'],length);rows=[]
 for cid,path in state.items():
  edges=[matches[u,v,s][0] for (u,_),(v,s) in zip(path,path[1:])];q=queries[cid]
  delay=rc.path(q['source'],q['sink'],edges)
  rows.append(dict(connection_id=cid,delay_integer=delay,physical_edge_ids=edges))
 if sha(route)!=before:raise ValueError('route changed during import')
 return state,rows,ledger
