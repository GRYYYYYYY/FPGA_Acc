"""Synchronous placement-update candidate staging with live-context restoration.

No bundle publication or concurrent readers. Unaffected route objects are shared
read-only with the live ledger; consumers must treat returned witnesses as immutable.
"""
from collections import Counter,defaultdict
from capacity_local_demand import CapacityLocalDemand,resident_query

def stage_reroute(state,endpoint_path,max_labels=10000):
 ctx=state.ctx
 if type(max_labels) is not int or max_labels<1:raise ValueError('positive label bound required')
 original_context=ctx.context;original_metadata=ctx.endpoint_metadata
 original_wire_owner=ctx.wire_owner_union
 original_wire_history=dict(ctx.history)
 original_other={n:ctx.native.other[n] for n in ctx.native.previous}
 try:
  affected=ctx.bind_endpoints(endpoint_path);nets=set(affected['affected_net_ids'])
  staged_metadata=ctx.endpoint_metadata
  # No old-path replay: resource ownership comes from the live perNET unions.
  unions=defaultdict(set,{net:used for net,used in state.unions.items() if net not in nets})
  parents=defaultdict(dict,{net:tree for net,tree in state.parents.items() if net not in nets})
  records={cid:r for cid,r in state.records.items() if r['net_id'] not in nets}
  ledger=Counter(state.ledger)
  for net in nets:ledger.subtract(state.unions.get(net,()))
  ledger+=Counter()
  events=[];failure=None;f=ctx.rc.fields
  local=CapacityLocalDemand(ctx.native);dirty=set()
  for q in sorted((q for q in ctx.context[5] if q['net_id'] in nets),key=lambda q:(NET_PRIORITY.get(q['net_id'],1000000),q['net_id'],q['connection_id'])):
   net=q['net_id'];ctx.set_wire_owner_union(unions[net]);answer=resident_query(ctx,local,ledger,unions[net],dirty,q['source'],q['sink'],BUDGETS.get(q['connection_id'],ctx.rc.scale//10**9),max_labels=max_labels);other=local.values;event={'query':q,'answer':answer,'committed':False,'wire_owner_union':sorted(unions[net])};events.append(event)
   if answer['status']!='FOUND':failure={'query':q,'status':answer['status']};break
   node=q['source'];used={node};incoming={}
   for eid in answer['physical_edge_ids']:
    u,n=state.slots[eid]
    if u!=node or n in used:raise ValueError('invalid search path')
    node=n;used.add(n);incoming[n]=(u,eid)
   if node!=q['sink'] or any(other.get(n,0)>=f['capacities'][n] for n in used):raise ValueError('invalid search endpoint/capacity')
   if any(n in parents[net] and parents[net][n]!=p for n,p in incoming.items()):failure={'query':q,'status':'MULTI_PARENT_REJECTED'};break
   parents[net].update(incoming);dirty.update(used-unions[net]);ledger.update(used-unions[net]);unions[net].update(used);records[q['connection_id']]={**q,'mode':'INCREMENTAL_HISTORY_DELAY','answer':answer};event['committed']=True
  return {'status':'COMPLETE_CANDIDATE' if failure is None else 'INCOMPLETE_NOT_PUBLISHABLE','failure':failure,'events':events,'records':[records[c] for c in sorted(records)],'ledger':dict(ledger),'affected':affected,'endpoint_metadata':staged_metadata,'history':dict(ctx.history),'scale':ctx.rc.scale,'graph_sha256':ctx.context[1],'completed_connections':len(records),'required_connections':len(ctx.context[5])}
 finally:
  ctx.context=original_context;ctx.endpoint_metadata=original_metadata
  ctx.restore_wire_state(original_wire_history,original_wire_owner)
  ctx.native.set_other(original_other)

def stage_reroute_with_repair(state,endpoint_path,max_labels=10000):
 """Stage incremental update plus max4 frontier-history repair; publish nothing."""
 import resident_four_repair_engine as engine
 ctx=state.ctx
 original_context=ctx.context;original_metadata=ctx.endpoint_metadata
 original_wire_owner=ctx.wire_owner_union
 original_wire_history=dict(ctx.history)
 original_history=dict(ctx.history)
 original_wire_owner=ctx.wire_owner_union
 original_other={n:ctx.native.other[n] for n in ctx.native.previous}
 try:
  incremental=stage_reroute(state,endpoint_path,max_labels=max_labels)
  if incremental['failure'] is None:
   return {'incremental':incremental,'repair':None,'status':incremental['status']}
  # The maintained repair policy has a fixed 10000-label budget.
  if max_labels!=10000 or incremental['failure']['status']!='UNREACHABLE':
   return {'incremental':incremental,'repair':None,'status':'INCOMPLETE_NOT_PUBLISHABLE'}
  ctx.bind_endpoints(endpoint_path)
  candidate=engine.repair_moved_history(ctx,incremental)
  return {'incremental':incremental,'repair':candidate,'status':candidate['status']}
 finally:
  ctx.context=original_context;ctx.endpoint_metadata=original_metadata
  ctx.restore_wire_state(original_history,original_wire_owner);ctx.native.set_other(original_other)

NET_PRIORITY={}

BUDGETS={}
