"""Persistent finite-bank collection and proof-supported physical detour feedback."""
import time
from collections import Counter
from pre_route_endpoints import sha
from finite_route_bank_cnf_v1 import encode
from certified_cnf_dependency_cdcl_v2 import solve
from independent_indexed_rup_verify_v1 import verify
from cnf_rup_support_indexed_v1 import support

def select(context,q,budgets,old,history):
 assert not context.closed and sha(context.graph)==context.digest
 inv=context.audit.inventory;rc=context.rc;search=context.search;length=context.length
 edge={eid:arc for arc,eid in inv.physical.arcs.items()};bank={cid:{} for cid in q}
 def add(cid,path,origin):
  if path[0]!=[q[cid]['source'],None] or path[-1][0]!=q[cid]['sink']:return
  delay,_,_=context.audit.certificate(path)
  if delay<=budgets[cid]:bank[cid].setdefault(tuple(tuple(x) for x in path),dict(path=path,origin=origin))
 for cid,path in old.items():add(cid,path,'AUTHENTICATED_HISTORY_BANK')
 for attempt in history['attempts']:
  for cid,path in attempt['paths'].items():add(int(cid),path,'AUTHENTICATED_HISTORY_BANK')
  for event in attempt['events']:
   if event['status']!='FOUND':continue
   cid=event['cid'];path=[[q[cid]['source'],None]]
   for eid in event['physical_edge_ids']:
    u,v,s=edge[eid];assert u==path[-1][0];path.append([v,s])
   add(cid,path,'AUTHENTICATED_HISTORY_BANK')
 rounds=[];solver_seconds=0.;paths=None
 for iteration in range(64):
  options={cid:list(opts.values()) for cid,opts in bank.items()}
  encoding=encode(options,q,{n:int(cap) for n,(_,cap) in inv.physical.nodes.items()})
  tick=time.perf_counter();result=solve(encoding['clauses'],len(encoding['variables']),10000);solver_seconds+=time.perf_counter()-tick
  verify(encoding['clauses'],result)
  row=dict(iteration=iteration,candidates=sum(map(len,options.values())),encoding=encoding,result=result,events=[])
  rounds.append(row)
  if result['status']=='SAT':
   paths={cid:next(option['path'] for i,option in enumerate(opts) if result['model'][encoding['path_vars'][f'{cid}:{i}']]) for cid,opts in options.items()};break
  if result['status']!='UNSAT':break
  core=support(encoding['clauses'],result);row['core_clause_indices']=core
  roles=[encoding['variables'][abs(lit)-1] for index in core for lit in encoding['clauses'][index]]
  cids=sorted({r['key'][0] for r in roles if r['kind']=='PATH'});blocked=sorted({r['key'][1] for r in roles if r['kind'] in ('NET_NODE','NET_PARENT')})
  before=sum(map(len,bank.values()))
  for cid in cids:
   for bans in [[n] for n in blocked]+[blocked]:
    if q[cid]['source'] in bans or q[cid]['sink'] in bans:continue
    scaled=budgets[cid]*rc.scale
    answer=search.query(q[cid]['source'],q[cid]['sink'],scaled.numerator//scaled.denominator,Counter({n:int(inv.physical.nodes[n][1]) for n in bans}),set(),{},100000,sum(length.values())+1)
    event=dict(cid=cid,blocked_nodes=bans,**answer);row['events'].append(event)
    if answer['status']=='FOUND':
     path=[[q[cid]['source'],None]]
     for eid in answer['physical_edge_ids']:
      u,v,s=edge[eid];assert u==path[-1][0];path.append([v,s])
     assert not set(bans)&{n for n,s in path};event['path']=path;add(cid,path,dict(iteration=iteration,blocked_nodes=bans))
  row['new_candidates']=sum(map(len,bank.values()))-before
  if not row['new_candidates']:break
 bank={cid:list(opts.values()) for cid,opts in bank.items()}
 if paths is not None:context.audit.validate(paths,q,budgets)
 assert sha(context.graph)==context.digest
 return dict(bank=bank,encoding=encoding,result=result,paths=paths,rounds=rounds)
