"""Independent complete production oracle callable inside a persistent workflow."""
from collections import defaultdict
from independent_route_cnf_structure_v1 import verify_encoding
from verify_certified_cnf_dependency_cdcl_v1 import verify

def audit(data,history,q,budgets,inv):
 bank={int(cid):opts for cid,opts in data['bank'].items()}
 def check(cid,path):
  assert path[0]==[q[cid]['source'],None] and path[-1][0]==q[cid]['sink']
  assert len({n for n,s in path})==len(path)
  r,c=inv.classes[inv.node_classes[path[0][0]]];delay=r*c/2
  for (u,_),(v,s) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,v,s))==1
   r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td
  assert delay<=budgets[cid]
 assert set(bank)==set(q)
 for cid,options in bank.items():
  for option in options:check(cid,option['path'])
 edge={eid:arc for arc,eid in inv.physical.arcs.items()}
 for row in data['rounds']:
  prefix={cid:[option for option in opts if not isinstance(option['origin'],dict) or option['origin']['iteration']<row['iteration']] for cid,opts in bank.items()}
  assert sum(map(len,prefix.values()))==row['candidates']
  verify_encoding(row['encoding'],prefix,q,inv);verify(row['encoding']['clauses'],row['result'])
  for event in row['events']:
   if event['status']!='FOUND':continue
   path=[[q[event['cid']]['source'],None]]
   for eid in event['physical_edge_ids']:
    u,v,s=edge[eid];assert u==path[-1][0];path.append([v,s])
   assert path==event['path'];check(event['cid'],path)
   assert not set(event['blocked_nodes'])&{n for n,s in path}
  assert row['result']['status'] in ('SAT','UNSAT','UNKNOWN_SEARCH_LIMIT')
 assert data['encoding']==data['rounds'][-1]['encoding'] and data['result']==data['rounds'][-1]['result']
 model={int(k):v for k,v in (data['result']['model'] or {}).items()}
 if data['paths'] is not None:
  paths={int(cid):path for cid,path in data['paths'].items()};assert set(paths)==set(q)
  owners=defaultdict(set);parents=defaultdict(set)
  for cid,path in paths.items():
   check(cid,path);net=q[cid]['net_id']
   selected=[option['path'] for i,option in enumerate(bank[cid]) if model[data['encoding']['path_vars'][f'{cid}:{i}']]]
   assert selected==[path]
   for n,s in path:owners[n].add(net)
   for (u,_),(v,s) in zip(path,path[1:]):parents[net,v].add((u,s))
  assert all(len(ns)<=int(inv.physical.nodes[n][1]) for n,ns in owners.items())
  assert all(len(ps)==1 for ps in parents.values())
 else:assert data['result']['status']!='SAT'

 history_events=0
 for attempt in history['attempts']:
  admitted={int(cid):path for cid,path in attempt['paths'].items()}
  owners=defaultdict(set);parents=defaultdict(set);by_net=defaultdict(set)
  for cid,path in admitted.items():
   check(cid,path);net=q[cid]['net_id'];by_net[net].add(cid)
   for n,s in path:owners[n].add(net)
   for (u,_),(v,s) in zip(path,path[1:]):parents[net,v].add((u,s))
  assert all(len(ns)<=int(inv.physical.nodes[n][1]) for n,ns in owners.items())
  assert all(len(ps)==1 for ps in parents.values())
  for net,cids in by_net.items():assert cids=={cid for cid,x in q.items() if x['net_id']==net}
  assert len(admitted)==attempt['admitted_connections']
  for event in attempt['events']:
   if event['status']!='FOUND':continue
   path=[[q[event['cid']]['source'],None]]
   for eid in event['physical_edge_ids']:
    u,v,s=edge[eid];assert u==path[-1][0];path.append([v,s])
   check(event['cid'],path);assert event.get('history_banned_node') not in {n for n,s in path};history_events+=1
 return dict(candidates=sum(map(len,bank.values())),rounds=len(data['rounds']),connections=len(data['paths']) if data['paths'] is not None else 0,successful_history_events_checked=history_events,status=data['result']['status'])
